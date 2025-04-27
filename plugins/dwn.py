import sys
import os
import asyncio
import re
import mimetypes
import pickle
import logging
import random
import string
import subprocess
import aiohttp

from yt_dlp import YoutubeDL
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from googleapiclient.discovery import build

from plugins.download import download_video, aria2c_media, google_drive

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Temporary memory storage
memory_store = {}
rename_store = {}

# Helper Functions
def extract_file_id(link):
    patterns = [r'/file/d/([a-zA-Z0-9_-]+)', r'id=([a-zA-Z0-9_-]+)']
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    return None

def human_readable_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def clean_filename(filename, mime=None):
    name, ext = os.path.splitext(filename)
    if not ext or ext == '':
        if mime:
            guessed_ext = mimetypes.guess_extension(mime)
            ext = guessed_ext if guessed_ext else '.mkv'
        else:
            ext = '.mkv'
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    name = name.strip('_')
    return name + ext

def generate_random_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

async def is_supported_by_ytdlp(url):
    try:
        cmd = ["yt-dlp", "--quiet", "--simulate", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False

async def get_ytdlp_info(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'unknown_file')
        filesize = info.get('filesize') or info.get('filesize_approx') or 0
        ext = info.get('ext', 'mp4')
        mime = f"video/{ext}"
    return title, filesize, mime

async def get_direct_file_info(url):
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

def get_drive_file_info(file_id):
    creds = pickle.load(open("/app/plugins/token.pickle", "rb"))
    service = build("drive", "v3", credentials=creds)
    file = service.files().get(fileId=file_id, fields="name, size, mimeType").execute()
    name = file.get("name")
    size = int(file.get("size", 0))
    mime = file.get("mimeType")
    return name, size, mime

# Main Handler
@Client.on_message(filters.private & filters.text)
async def universal_handler(client, message):
    text = message.text.strip()

    if not text.startswith("http"):
        return

    chat_id = message.chat.id

    if "drive.google.com" in text:
        await message.reply("📥 Google Drive link detected! Fetching file details...")
        file_id = extract_file_id(text)
        if not file_id:
            return await message.reply("❌ Invalid Google Drive link.")

        try:
            name, size, mime = get_drive_file_info(file_id)
            size_str = human_readable_size(size)
            clean_name = clean_filename(name, mime)
            random_id = generate_random_id()

            memory_store[random_id] = {
                "link": text,
                "filename": clean_name,
                "source": "gdrive"
            }

            info_message = f"📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`"
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Default", callback_data=f"default|{random_id}"),
                    InlineKeyboardButton("✏️ Rename", callback_data=f"rename|{random_id}")
                ]
            ])

            await message.reply(info_message, reply_markup=buttons)

        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    else:
        await message.reply("📥 Checking link type...")

        try:
            if await is_supported_by_ytdlp(text):
                await message.reply("🔗 Supported by yt-dlp! Fetching details...")
                title, filesize, mime = await get_ytdlp_info(text)
                size_str = human_readable_size(filesize)
                clean_name = clean_filename(title, mime)
                random_id = generate_random_id()

                memory_store[random_id] = {
                    "link": text,
                    "filename": clean_name,
                    "source": "ytdlp"
                }

                info_message = f"📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`"
                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Default", callback_data=f"default|{random_id}"),
                        InlineKeyboardButton("✏️ Rename", callback_data=f"rename|{random_id}")
                    ]
                ])

                await message.reply(info_message, reply_markup=buttons)

            else:
                await message.reply("🔗 Direct link detected! Fetching details...")
                name, size, mime = await get_direct_file_info(text)
                size_str = human_readable_size(size)
                clean_name = clean_filename(name, mime)
                random_id = generate_random_id()

                memory_store[random_id] = {
                    "link": text,
                    "filename": clean_name,
                    "source": "direct"
                }

                info_message = f"📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`"
                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Default", callback_data=f"default|{random_id}"),
                        InlineKeyboardButton("✏️ Rename", callback_data=f"rename|{random_id}")
                    ]
                ])

                await message.reply(info_message, reply_markup=buttons)

        except Exception as e:
            await message.reply(f"❌ Error: {e}")

# Button Handler
@Client.on_callback_query()
async def button_handler(client, callback_query):
    data = callback_query.data
    action, random_id = data.split('|')

    file_info = memory_store.get(random_id)
    if not file_info:
        await callback_query.answer("❌ Session expired. Please try again.", show_alert=True)
        return

    link = file_info['link']
    filename = file_info['filename']
    source = file_info['source']
    chat_id = callback_query.message.chat.id

    if action == "rename":
        rename_store[chat_id] = (link, source, random_id)
        await callback_query.message.reply("✏️ Send me new filename (with extension):")

    elif action == "default":
        await callback_query.message.delete()
        await start_download(client, chat_id, link, filename, source)

# Rename Handler
@Client.on_message(filters.private & filters.text)
async def rename_handler(client, message):
    chat_id = message.chat.id
    if chat_id in rename_store:
        link, source, random_id = rename_store.pop(chat_id)
        new_filename = message.text.strip()
        memory_store[random_id]['filename'] = new_filename
        await message.reply(f"✅ Filename changed to `{new_filename}`\n\nStarting download...")
        await start_download(client, chat_id, link, new_filename, source)

# Download starter
async def start_download(client, chat_id, link, filename, source):
    if source == "gdrive":
        await google_drive(client, chat_id, filename, link)
    elif source == "ytdlp":
        await download_video(client, chat_id, link)
    elif source == "direct":
        await aria2c_media(client, chat_id, link, filename)
