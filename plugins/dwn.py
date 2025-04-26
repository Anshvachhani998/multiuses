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
        # Google Drive link detected
        await message.reply("📥 Google Drive link detected! Fetching file details...")

        # Extract file ID from Google Drive link
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
        await message.reply("📥 Downloading via direct/YouTube method...")
        await aria2c_media(client, chat_id, text)

