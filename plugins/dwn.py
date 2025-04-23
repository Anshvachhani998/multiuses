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
        try:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
        except Exception as e:
            raise Exception(f"❌ Error downloading video: {str(e)}")

async def upload_to_telegram(filename, chat_id, url):
    try:
        # Send the downloaded file to the Telegram chat
        await Client.send_document(chat_id=chat_id, document=filename, caption=f"Downloaded from: {url}")
        os.remove(filename)  # Clean up after upload
        print("✅ File uploaded and removed from disk.")
    except Exception as e:
        print(f"❌ Error uploading: {e}")

async def handle_url(url, chat_id):
    try:
        print(f"🔍 Checking URL: {url}")
        # Download the video
        filename = download_video(url)
        print(f"⬇️ Downloaded: {filename}")
        # Upload to Telegram
        await upload_to_telegram(filename, chat_id, url)
    except Exception as e:
        print(f"❌ Error: {e}")
        # Send an error message to the user
        await Client.send_message(chat_id, f"Sorry, something went wrong: {str(e)}")


# Handle /url command
@Client.on_message(filters.command("url"))
async def dwn(client, message):
    try:
        # Check if the user provided a URL
        if len(message.text.split(' ')) < 2:
            await message.reply("❌ Please provide a valid URL after the command.")
            return

        # Extract the URL from the command
        url = message.text.split(' ', 1)[1]  # Get the URL after the /url command
        chat_id = message.chat.id  # Get the chat ID of the user
        
        # Notify user that the URL is being processed
        await message.reply("🔄 Processing your link... Please wait.")
        
        # Start handling the URL
        await handle_url(url, chat_id)
    except Exception as e:
        # General error handling
        await message.reply(f"❌ An error occurred: {str(e)}")
