import sys
import os
import asyncio
from yt_dlp import YoutubeDL
from pyrogram import Client, filters
from plugins.download import download_video, aria2c_media, google_drive


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def handle_url(client, url, chat_id):
    try:
        print(f"🔍 Checking URL: {url}")
        filename = await google_drive(client, chat_id, url)
    except Exception as e:
        print(f"❌ Errower: {e}")

@Client.on_message(filters.command("url"))
async def dwn(client, message):
    try:
        if len(message.text.split(' ')) < 2:
            await message.reply("❌ Please provide a valid URL after the command.")
            return

        url = message.text.split(' ', 1)[1]
        chat_id = message.chat.id

        await message.reply("🔄 Processing your link... Please wait.")
        await handle_url(client, url, chat_id)
    except Exception as e:
        await message.reply(f"❌ An error occurred: {str(e)}")



from pyrogram import Client, filters
import pickle
import re
from googleapiclient.discovery import build

import pickle
import re
from googleapiclient.discovery import build
from pyrogram import Client, filters

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
    creds = pickle.load(open("/root/URL-UPLOADER/plugins/token.pickle", "rb"))
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

# Pyrogram command to handle /gdrive request
@Client.on_message(filters.command("gdrive") & filters.private)
async def info_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("❗ Usage: `/info <Google Drive Link>`", quote=True)

    link = message.command[1]
    file_id = extract_file_id(link)

    if not file_id:
        return await message.reply("❌ Invalid Google Drive link!", quote=True)

    try:
        # Get file details
        name, size, mime = get_file_info(file_id)
        size_str = human_readable_size(size)
        await message.reply(f"📄 **File Name:** `{name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`", quote=True)

    except Exception as e:
        import os  # make sure to import os at the top
        cwd = os.getcwd()
        await message.reply(f"❌ Error: {e}\n📁 Current Dir: `{cwd}`", quote=True)

