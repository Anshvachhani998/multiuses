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
import subprocess
import json

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from googleapiclient.discovery import build
from plugins.download import download_video, aria2c_media, google_drive
from database.db import db
from utils import active_tasks
from info import LOG_CHANNEL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def is_direct_download_link(url: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=5) as resp:
                content_type = resp.headers.get("Content-Type", "")
                return any(x in content_type for x in ["video/", "audio/", "application/"])
    except:
        return False
        
async def get_terabox_info(link):
    api_url = f"https://teraboxdl-sjjs-projects.vercel.app/api?link={link}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status != 200:
                    return {"error": f"HTTP {response.status}"}
                data = await response.json()

        info = data.get("Extracted Info", [])[0] if data.get("Extracted Info") else None
        if not info:
            return {"error": "No extracted info found."}

        return {
            "title": info.get("Title"),
            "size": info.get("Size"),
            "download_url": info.get("Direct Download Link")
        }

    except Exception as e:
        return {"error": str(e)}

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

def get_file_info(file_id):
    creds = pickle.load(open("/app/plugins/token.pickle", "rb"))
    service = build("drive", "v3", credentials=creds)
    file = service.files().get(fileId=file_id, fields="name, size, mimeType").execute()
    name = file.get("name")
    size = int(file.get("size", 0))
    mime = file.get("mimeType")
    return name, size, mime
    
async def is_supported_by_ytdlp(url):
     try:
         cmd = ["yt-dlp", "--quiet", "--simulate", url]
         result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
 
         return result.returncode == 0
     except Exception:
         return False

def clean_filename(filename, mime=None):
    # Get the name and extension from the filename
    name, ext = os.path.splitext(filename)
    
    # Normalize the extension to lowercase
    ext = ext.lower() if ext else ''

    if not ext:
        if mime:
            # If mime type is provided, guess the extension
            guessed_ext = mimetypes.guess_extension(mime)
            ext = guessed_ext if guessed_ext else '.mkv'
        else:
            ext = '.mkv'

    # Clean the file name
    name = re.sub(r'[^\w\s-]', '', name)  # Remove unwanted characters
    name = re.sub(r'[-\s]+', '_', name)  # Replace spaces and hyphens with underscores
    name = name.strip('_')  # Remove leading/trailing underscores

    # Return cleaned filename with correct extension
    return name + ext


@Client.on_message(filters.private & filters.text)
async def universal_handler(client, message):
    text = message.text.strip()
    if not (text.startswith("http") or text.startswith("magnet:") or text.endswith(".torrent")):
        return

    chat_id = message.chat.id
    checking_msg = await message.reply_text("**🔎 Checking your link, please wait...**")
    
    if "youtube.com" in text or "youtu.be" in text:
        await checking_msg.delete()
        await checking_msg.edit("**⚠️ YouTube links are not supported here.**\n\n**👉 Please use @FastYouTubeDLBot for downloading YouTube videos.**")
        return

    if "instagram.com" in text:
        await checking_msg.delete()
        await checking_msg.edit("**⚠️ Instagram links are not supported here.**\n\n**👉 Please use @NewInstaReelsDownloadBot for downloading Instagram media.**")
        return
        
    if not await db.check_task_limit(chat_id):
        await checking_msg.delete()
        await message.reply_text(
            "❌ **You have reached your daily task limit! Try again tomorrow.**\n\n"
            "**Use /mytasks to check your remaining quota.**"
        )
        return

    if active_tasks.get(chat_id):
        await checking_msg.delete()
        await message.reply_text("⏳ **Your previous task is still running. Please wait!**")
        return

    try:
        if "drive.google.com" in text:
            if "drive/folders" in text:
                # Google Drive Folder Error
                await checking_msg.edit("❌ **Google Drive folder download is not supported yet.**\n\n📦 **Feature coming soon...**")
                
                err_msg = (
                    f"📁 <b>Google Drive Folder Attempt</b>\n"
                    f"👤 <b>User:</b> <a href='tg://user?id={chat_id}'>{chat_id}</a>\n"
                    f"🔗 <b>Link:</b> <a href='{text}'>Click here</a>\n"
                )
                await client.send_message(LOG_CHANNEL, err_msg, parse_mode="html")
                return

            file_id = extract_file_id(text)
            if not file_id:
                # Invalid Google Drive link error
                await checking_msg.edit("** Invalid Google Drive link.**")
                
                err_msg = (
                    f"🚨 <b>Invalid Google Drive Link</b>\n"
                    f"👤 <b>User:</b> <a href='tg://user?id={chat_id}'>{chat_id}</a>\n"
                    f"🔗 <b>Link:</b> <a href='{text}'>Click here</a>\n"
                )
                await client.send_message(LOG_CHANNEL, err_msg)
                return

            name, size, mime = get_file_info(file_id)
            checking = await checking_msg.edit(f"✅ Processing Google Drive link...")
            logging.info(name)
            clean = clean_filename(name, mime)
            logging.info(clean)
            await google_drive(client, chat_id, text, clean, checking)

        elif "terabox.com" in text:
            checking = await checking_msg.edit("✅ Processing TeraBox link...")
            terabox_info = await get_terabox_info(text)
            logging.info(terabox_info)
            if "error" in terabox_info:
                # Invalid TeraBox link error
                await checking_msg.edit("**Invalid TeraBox link.**")
                
                err_msg = (
                    f"🚨 <b>Invalid TeraBox Link</b>\n"
                    f"👤 <b>User:</b> <a href='tg://user?id={chat_id}'>{chat_id}</a>\n"
                    f"🔗 <b>Link:</b> <a href='{text}'>Click here</a>\n"
                )
                await client.send_message(LOG_CHANNEL, err_msg)
                return
                
            dwn = terabox_info.get("download_url")
            await aria2c_media(client, chat_id, dwn, checking)

        elif "magnet:" in text:
            checking = await checking_msg.edit("✅ Processing magnet link...")
            await aria2c_media(client, chat_id, text, checking)

        elif ".torrent" in text:
            checking = await checking_msg.edit("✅ Processing torrent link...")
            await aria2c_media(client, chat_id, text, checking)

        elif await is_direct_download_link(text):
            checking = await checking_msg.edit("✅ Direct download link detected. Starting download...")
            await aria2c_media(client, chat_id, text, checking)

        elif await is_supported_by_ytdlp(text):
            try:
                checking = await checking_msg.edit("✅ Fetching file info...")

                info = await get_video_info(text)  # 👈 aapka custom info fetcher
                if not info:
                    await checking.edit("❌ Failed to fetch video info.")
                    return

                title = info.get("title", "Unknown Title")
                filesize = info.get("filesize", "Unknown size")
                fmt = info.get("format", "N/A")
                cleaned = clean_filename(title)  # 👈 optional cleaner

                caption = (
                    f"**🎬 Title:** `{title}`\n"
                    f"**📦 Size:** `{filesize}`\n"
                    f"**🔰 Format:** `{fmt}`\n\n"
                    f"**✅ Click below to start download.**"
                )

                btn = [[
                    InlineKeyboardButton("📥 Download Now", callback_data=f"ytdlp|{text}")
                ]]

                await checking.edit(
                    caption,
                    reply_markup=InlineKeyboardMarkup(btn)
                )

            except Exception as e:
                logger.error(f"YTDLP link processing error: {e}")
                await checking_msg.edit("❌ Failed to process the link.")


        else:
            # If none of the supported link formats match
            await checking_msg.edit("**This link is not accessible or not direct download link**")
            err_msg = (
                f"🚨 <b>Link Not Found</b>\n"
                f"👤 <b>User:</b> <a href='tg://user?id={chat_id}'>{chat_id}</a>\n"
                f"🔗 <b>Link:</b> <a href='{text}'>Click here</a>\n"
            )
            await client.send_message(LOG_CHANNEL, err_msg)

    except Exception as e:
        logger.error(f"Error: {e}")
        await checking_msg.edit("**This link is not accessible or not direct download link**")

        err_msg = (
            f"🚨 <b>Link Handling Error</b>\n"
            f"👤 <b>User:</b> <a href='tg://user?id={chat_id}'>{chat_id}</a>\n"
            f"🔗 <b>Link:</b> <a href='{text}'>Click here</a>\n"
            f"⚠️ <b>Error:</b> <code>{str(e)}</code>"
        )

        try:
            await client.send_message(LOG_CHANNEL, err_msg)
        except Exception as log_err:
            logger.error(f"Failed to log to channel: {log_err}")



import mimetypes

async def get_video_info(url: str) -> dict:
    try:
        # Run yt-dlp -j command to get JSON info
        command = ['yt-dlp', '-j', url]
        result = await asyncio.to_thread(subprocess.check_output, command)
        info_dict = json.loads(result.decode('utf-8'))

        # Extract values
        title = info_dict.get("title", "Unknown Title")
        filesize = info_dict.get("filesize") or info_dict.get("filesize_approx") or 0
        ext = info_dict.get("ext", "unknown")

        # Get mime type from extension
        mime = mimetypes.types_map.get(f".{ext}", "application/octet-stream")

        return {
            "title": title,
            "filesize": filesize,
            "mime": mime
        }

    except Exception as e:
        print(f"[get_video_info] Error: {e}")
        return None
