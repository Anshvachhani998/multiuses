import sys
import os
import asyncio
import re
import logging
import mimetypes
import pickle
import aiohttp
import subprocess
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from googleapiclient.discovery import build
from plugins.download import download_video, aria2c_media, google_drive

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# File ID Extraction for GDrive
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

# GDrive File Info
def get_file_info(file_id):
    creds = pickle.load(open("/app/plugins/token.pickle", "rb"))
    service = build("drive", "v3", credentials=creds)
    file = service.files().get(fileId=file_id, fields="name, size, mimeType").execute()
    name = file.get("name")
    size = int(file.get("size", 0))
    mime = file.get("mimeType")
    return name, size, mime

# File Size Formatter
def human_readable_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

# Clean Filename
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

# Check if supported by yt-dlp
async def is_supported_by_ytdlp(url):
    try:
        cmd = ["yt-dlp", "--quiet", "--simulate", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False

# yt-dlp Info
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

# Direct Link File Info
async def get_file_info_from_url(url):
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.head(url, allow_redirects=True) as response:
                if response.status != 200:
                    raise Exception(f"Status: {response.status}")
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
    except Exception as e:
        raise Exception(f"Failed to fetch info: {str(e)}")

# Universal Handler
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
            name, size, mime = get_file_info(file_id)
            size_str = human_readable_size(size)
            clean_name = clean_filename(name, mime)

            info_message = (
                f"📄 **File Name:** `{clean_name}`\n"
                f"📦 **Size:** `{size_str}`\n"
                f"🧾 **MIME Type:** `{mime}`"
            )
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Default", callback_data=f"gdrive_default|{text}|{clean_name}"),
                    InlineKeyboardButton("✏️ Rename", callback_data=f"gdrive_rename|{text}|{clean_name}")
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
                name, size, mime = await get_ytdlp_info(text)
                size_str = human_readable_size(size)
                clean_name = clean_filename(name, mime)

                info_message = (
                    f"📄 **File Name:** `{clean_name}`\n"
                    f"📦 **Size:** `{size_str}`\n"
                    f"🧾 **MIME Type:** `{mime}`"
                )
                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Default", callback_data=f"ytdlp_default|{text}|{clean_name}"),
                        InlineKeyboardButton("✏️ Rename", callback_data=f"ytdlp_rename|{text}|{clean_name}")
                    ]
                ])
                await message.reply(info_message, reply_markup=buttons)

            else:
                await message.reply("🔗 Direct link detected! Fetching details...")
                name, size, mime = await get_file_info_from_url(text)
                size_str = human_readable_size(size)
                clean_name = clean_filename(name, mime)

                info_message = (
                    f"📄 **File Name:** `{clean_name}`\n"
                    f"📦 **Size:** `{size_str}`\n"
                    f"🧾 **MIME Type:** `{mime}`"
                )
                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Default", callback_data=f"direct_default|{text}|{clean_name}"),
                        InlineKeyboardButton("✏️ Rename", callback_data=f"direct_rename|{text}|{clean_name}")
                    ]
                ])
                await message.reply(info_message, reply_markup=buttons)

        except Exception as e:
            await message.reply(f"❌ Error: {e}")

# Button Handler
@Client.on_callback_query()
async def button_handler(client, callback_query):
    data = callback_query.data
    parts = data.split('|')
    action = parts[0]
    link = parts[1]
    filename = parts[2]

    chat_id = callback_query.message.chat.id

    if "rename" in action:
        await callback_query.message.reply("✏️ Send me the new file name (with extension):")
        client.rename_info[chat_id] = (action, link)
    elif "default" in action:
        await callback_query.message.delete()
        await start_download(client, chat_id, action, link, filename)

# Text Handler for Rename
@Client.on_message(filters.private & filters.text)
async def rename_handler(client, message):
    chat_id = message.chat.id

    if chat_id in client.rename_info:
        action, link = client.rename_info.pop(chat_id)
        new_filename = clean_filename(message.text)

        await message.reply(f"✅ New filename set: `{new_filename}`\n\nStarting download...")

        await start_download(client, chat_id, action, link, new_filename)

# Start Download Based on Source
async def start_download(client, chat_id, action, link, filename):
    if action.startswith("gdrive"):
        await google_drive(client, chat_id, filename, link)
    elif action.startswith("ytdlp"):
        await download_video(client, chat_id, link)
    elif action.startswith("direct"):
        await aria2c_media(client, chat_id, filename, link)
