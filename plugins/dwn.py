import sys
import os
import asyncio
import re
from yt_dlp import YoutubeDL
from pyrogram import Client, filters
from plugins.download import download_video, aria2c_media, google_drive
import mimetypes
import pickle
import re
from googleapiclient.discovery import build
from pyrogram import Client, filters
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Function to extract file ID from Google Drive link
def extract_file_id(link):
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',  # Pattern for /file/d/ID
        r'id=([a-zA-Z0-9_-]+)'        # Pattern for id=ID
    ]
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    return None

# Function to get file details from Google Drive using Google API
def get_file_info(file_id):
    creds = pickle.load(open("/app/plugins/token.pickle", "rb"))
    service = build("drive", "v3", credentials=creds)
    file = service.files().get(fileId=file_id, fields="name, size, mimeType").execute()
    name = file.get("name")
    size = int(file.get("size", 0))
    mime = file.get("mimeType")
    return name, size, mime

# Function to format file size into human-readable format
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

    # Clean the name
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    name = name.strip('_')

    return name + ext

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
            return await message.reply("❌ Invalid Google Drive link.", quote=True)

        try:
            name, size, mime = get_file_info(file_id)
            size_str = human_readable_size(size)
            clean_name = clean_filename(name, mime)

            info_message = f"📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`"
            await message.reply(info_message, quote=True)

            await google_drive(client, chat_id, clean_name, text)

        except Exception as e:
            await message.reply(f"❌ Error: {e}", quote=True)

    else:
        await message.reply("📥 Fetching file info for direct/YouTube link...")

        try:
            # Fetch info using aria2c
            name, size, mime = await aria2c_get_info(text)
            size_str = human_readable_size(size)
            clean_name = clean_filename(name, mime)

            info_message = f"📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`"
            await message.reply(info_message, quote=True)

            await aria2c_media(client, chat_id, text, filename=clean_name)

        except Exception as e:
            await message.reply(f"❌ Error: {e}", quote=True)


import subprocess
import re

async def aria2c_get_info(url):
    url = url.strip().replace('\r', '').replace('\n', '')
    if not url:
        raise Exception("No URL provided for fetching file info.")

    try:
        logging.info(f"Fetching file info from URL: {url}")

        cmd = [
            "aria2c",
            "--head",
            url
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(f"aria2c error: {stderr}")

        logging.info(f"aria2c output:\n{stdout}")  # ✅ Corrected logging

        filename = None
        size = None
        mime = None

        filename_match = re.search(r'filename="([^"]+)"', stdout)
        if filename_match:
            filename = filename_match.group(1)

        size_match = re.search(r'Content-Length:\s*(\d+)', stdout)
        if size_match:
            size = int(size_match.group(1))

        mime_match = re.search(r'Content-Type:\s*([^;]+)', stdout)
        if mime_match:
            mime = mime_match.group(1)

        if not filename:
            filename = "downloaded_file"

        return filename, size, mime

    except Exception as e:
        raise Exception(f"Error fetching file info: {str(e)}")
