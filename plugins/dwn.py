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
