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
import uuid
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from googleapiclient.discovery import build
from plugins.download import download_video, aria2c_media, google_drive
from database.db import db
from utils import (
    active_tasks, format_size, get_ytdlp_info,
    extract_file_id, get_file_info, clean_filename,
    get_terabox_info, is_direct_download_link,
    is_supported_by_ytdlp, ytdlp_clean, clean_terabox
)
from info import LOG_CHANNEL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def process_terabox_link(client, chat_id, link, checking_msg):
    terabox_info = await get_terabox_info(link)
    if "error" in terabox_info:
        await checking_msg.edit(f"❌ **Invalid TeraBox link**.")
        return
    
    file_name = terabox_info.get("title", "Unknown File")
    file_size = terabox_info.get("size", "Unknown Size")
    file_url = terabox_info.get("download_url", "")
    

    mime, file_extension = mimetypes.guess_type(file_name)
    mime = mime or "application/octet-stream"
    ext = file_extension or "unknown"

    clean_name = clean_terabox(file_name)

    caption = f"**🎬 Title:** `{clean_name}`\n"
    caption += f"**📦 Size:** `{file_size}`\n"
    caption += f"**🔰 Mime:** `{mime}`\n"
    
    caption += f"**✅ Click below to start download.**"

    btn = [[
        InlineKeyboardButton("📥 Download Now", callback_data=f"terabox")
    ]]
    
    await checking_msg.edit(
        caption,
        reply_markup=InlineKeyboardMarkup(btn)
    )

async def process_ytdlp_link(client, chat_id, link, checking_msg):
    try:
        info = await get_ytdlp_info(link)
        if not info:
            await checking_msg.edit("❌ Failed to fetch video info.")
            return

        try:
            file_size = int(info.get("filesize", 0))
        except (ValueError, TypeError):
            file_size = 0
        mime = info.get("mime", "application/octet-stream")
        raw_title = info.get("title", "").strip()

        if not raw_title or raw_title.lower() == "unknown title":
            raw_title = f"{uuid.uuid4().hex[:8]}"

        clean = ytdlp_clean(raw_title)


        caption = f"**🎬 Title:** `{clean}`\n"
        if file_size:
            caption += f"**📦 Size:** `{format_size(file_size)}`\n"
        caption += f"**🔰 Mime:** `{mime}`\n"
        caption += f"**✅ Click below to start download.**"

        btn = [[InlineKeyboardButton("📥 Download Now", callback_data="ytdlp")]]
        await checking_msg.edit(caption, reply_markup=InlineKeyboardMarkup(btn))

    except Exception as e:
        logger.error(f"YTDLP processing error: {e}")
        await checking_msg.edit("❌ Error processing the YouTube link.")


async def process_gdrive_link(client, chat_id, link, checking_msg):
    file_id = extract_file_id(link)
    if not file_id:
        await checking_msg.edit("❌ Invalid Google Drive link.")
        return

    name, size, mime = get_file_info(file_id)
    logging.info(f" done{name}")
    clean = clean_filename(name, mime)

    caption = f"**🎬 Title:** `{clean}`\n"
    caption += f"**📦 Size:** `{format_size(size) if isinstance(size, (int, float)) else size}`\n"
    caption += f"**🔰 Mime:** `{mime}`\n"
    caption += f"**✅ Click below to start download.**"

    btn = [[InlineKeyboardButton("📥 Download Now", callback_data=f"gdrive:{file_id}|{clean}")]]
    await checking_msg.edit(caption, reply_markup=InlineKeyboardMarkup(btn))


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

            checking = await checking_msg.edit(f"✅ Processing Google Drive link...")
            await process_gdrive_link(client, chat_id, text, checking)

        elif "terabox.com" in text:
            checking = await checking_msg.edit("✅ Processing TeraBox link...")
            await process_terabox_link(client, chat_id, text, checking)

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
            checking = await checking_msg.edit("✅ Fetching file info...")
            await process_ytdlp_link(client, chat_id, text, checking)

        else:
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
