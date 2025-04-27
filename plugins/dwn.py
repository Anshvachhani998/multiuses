import sys
import os
import asyncio
import re
import mimetypes
import pickle
import subprocess
import logging
import aiohttp
import yt_dlp

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.download import download_video, aria2c_media, google_drive
from googleapiclient.discovery import build

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Memory to track rename requests
user_rename_requests = {}

# Extract file ID from Google Drive link
def extract_file_id(link):
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    return None

# Get file info from Google Drive
def get_file_info(file_id):
    creds = pickle.load(open("/app/plugins/token.pickle", "rb"))
    service = build("drive", "v3", credentials=creds)
    file = service.files().get(fileId=file_id, fields="name, size, mimeType").execute()
    name = file.get("name")
    size = int(file.get("size", 0))
    mime = file.get("mimeType")
    return name, size, mime

# Format size
def human_readable_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

# Clean filename
def clean_filename(filename, mime=None):
    name, ext = os.path.splitext(filename)
    if not ext:
        if mime:
            guessed_ext = mimetypes.guess_extension(mime)
            ext = guessed_ext if guessed_ext else '.mkv'
        else:
            ext = '.mkv'
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    name = name.strip('_')
    return name + ext

# Check if yt-dlp supports link
async def is_supported_by_ytdlp(url):
    try:
        cmd = ["yt-dlp", "--quiet", "--simulate", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

# Get yt-dlp info
async def get_ytdlp_info(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'unknown_file')
        filesize = info.get('filesize') or info.get('filesize_approx') or 0
        ext = info.get('ext', 'mp4')
        mime = f"video/{ext}"
    return title, filesize, mime

# Get file info for direct link
async def get_direct_link_info(url):
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True, timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch file info. Status code: {response.status}")
                headers = response.headers
                filename = None
                if 'Content-Disposition' in headers:
                    dispo = headers['Content-Disposition']
                    filename_match = re.search(r'filename="?([^"]+)"?', dispo)
                    if filename_match:
                        filename = filename_match.group(1)
                size = int(headers.get('Content-Length', 0))
                mime = headers.get('Content-Type', None)
                if not filename:
                    filename = "downloaded_file"
                return filename, size, mime
    except asyncio.TimeoutError:
        raise Exception("❌ Error: Timeout exceeded while fetching file info.")
    except Exception as e:
        raise Exception(f"❌ Error: {str(e)}")

# Start download according to type
async def start_download(client, chat_id, url, filename, link_type):
    if link_type == "gdrive":
        await google_drive(client, chat_id, filename, url)
    elif link_type == "yt-dlp":
        await download_video(client, chat_id, url, filename)
    elif link_type == "direct":
        await aria2c_media(client, chat_id, url, filename)
    else:
        await client.send_message(chat_id, "❌ Unknown link type. Cannot download.")

# Message Handler
@Client.on_message(filters.private & filters.text)
async def universal_handler(client, message):
    chat_id = message.chat.id
    text = message.text.strip()

    if not text.startswith("http"):
        return

    if chat_id in user_rename_requests:
        url, old_filename, link_type = user_rename_requests.pop(chat_id)
        new_filename = text
        await message.reply(f"✅ Starting download with renamed filename `{new_filename}`...")
        await start_download(client, chat_id, url, new_filename, link_type)
        return

    if "drive.google.com" in text:
        await message.reply("📥 Google Drive link detected! Fetching file details...")
        file_id = extract_file_id(text)
        if not file_id:
            return await message.reply("❌ Invalid Google Drive link.")
        try:
            name, size, mime = get_file_info(file_id)
            size_str = human_readable_size(size)
            clean_name = clean_filename(name, mime)

            info_message = f"📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`"

            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Default", callback_data=f"default|{clean_name}|{text}|gdrive"),
                 InlineKeyboardButton("✏️ Rename", callback_data=f"rename|{clean_name}|{text}|gdrive")]
            ])

            await message.reply(info_message, reply_markup=buttons)

        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    else:
        await message.reply("📥 Checking link type...")
        try:
            if await is_supported_by_ytdlp(text):
                name, size, mime = await get_ytdlp_info(text)
                size_str = human_readable_size(size)
                clean_name = clean_filename(name, mime)

                info_message = f"📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`"

                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Default", callback_data=f"default|{clean_name}|{text}|yt-dlp"),
                     InlineKeyboardButton("✏️ Rename", callback_data=f"rename|{clean_name}|{text}|yt-dlp")]
                ])

                await message.reply(info_message, reply_markup=buttons)

            else:
                name, size, mime = await get_direct_link_info(text)
                size_str = human_readable_size(size)
                clean_name = clean_filename(name, mime)

                info_message = f"🔗 **Direct Link Detected**\n\n📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`"

                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Default", callback_data=f"default|{clean_name}|{text}|direct"),
                     InlineKeyboardButton("✏️ Rename", callback_data=f"rename|{clean_name}|{text}|direct")]
                ])

                await message.reply(info_message, reply_markup=buttons)

        except Exception as e:
            await message.reply(f"❌ Error: {e}")

# Button Callback Handler
@Client.on_callback_query()
async def button_handler(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id

    try:
        action, filename, url, link_type = data.split("|", 3)
    except ValueError:
        return await callback_query.answer("❌ Invalid data.", show_alert=True)

    if action == "default":
        await callback_query.message.edit_text("✅ Starting download with default filename...")
        await start_download(client, chat_id, url, filename, link_type)

    elif action == "rename":
        await callback_query.message.edit_text("✏️ Send me the new filename with extension (example: `newfile.mp4`)!")
        user_rename_requests[chat_id] = (url, filename, link_type)
