import sys
import os
from yt_dlp import YoutubeDL
from pyrogram import Client, filters

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_video(url):
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

async def upload_to_telegram(filename, chat_id, url):
    try:
        await Client.send_document(chat_id=chat_id, document=filename, caption=f"Downloaded from: {url}")
        os.remove(filename)  # Clean up after upload
        print("✅ File uploaded and removed from disk.")
    except Exception as e:
        print(f"❌ Error uploading: {e}")

async def handle_url(url, chat_id):
    try:
        print(f"🔍 Checking URL: {url}")
        filename = download_video(url)
        print(f"⬇️ Downloaded: {filename}")
        await upload_to_telegram(filename, chat_id, url)
    except Exception as e:
        print(f"❌ Error: {e}")

# Handle /url command
@Client.on_message(filters.command("url"))
async def dwn(client, message):
    # Extract the URL from the command
    url = message.text.split(' ', 1)[1]  # Get the URL after the /url command
    chat_id = message.chat.id  # Get the chat ID of the user
    
    # Start handling the URL
    await handle_url(url, chat_id)
