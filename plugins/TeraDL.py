import os
import io
import re
import logging
import yt_dlp
import aiohttp
import aiofiles
import asyncio
import time
import math
import random
import string
import psutil
import requests
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread
from PIL import Image
import uuid
import ffmpeg
from math import ceil


TERABOX_REGEX = r"(https?://[^\s]*tera[^\s]*)"

def get_terabox_info(link):
    api_url = f"https://tera-dl.vercel.app/api?link={link}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        info = data.get("Extracted Info", [])[0] if data.get("Extracted Info") else None
        if not info:
            return {"error": "No extracted info found."}

        return {
            "title": info.get("Title"),
            "size": info.get("Size"),
            "download_url": info.get("Direct Download Link"),
            "thumbnail": info.get("Thumbnails", {}).get("360x270")
        }

    except Exception as e:
        return {"error": str(e)}

async def progress_bar(current, total, status_message, start_time, last_update_time, lebel):
    """Display a progress bar for downloads/uploads."""
    try:
        if total == 0:
            return  # Prevent division by zero

        elapsed_time = time.time() - start_time
        percentage = (current / total) * 100
        speed = current / elapsed_time / 1024 / 1024  # Speed in MB/s
        uploaded = current / 1024 / 1024
        total_size = total / 1024 / 1024
        remaining_size = total_size - uploaded
        eta = (remaining_size / speed) if speed > 0 else 0

        eta_min = int(eta // 60)
        eta_sec = int(eta % 60)

        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        # Throttle updates
        if time.time() - last_update_time[0] < 2:
            return
        last_update_time[0] = time.time()

        progress_blocks = int(percentage // 5)
        progress_bar_str = "■" * progress_blocks + "□" * (20 - progress_blocks)

        text = (
            f"**╭─────{lebel}─────〄**\n"
            "**│**\n"
            f"**├📁 Sɪᴢᴇ : {humanbytes(current)} ✗ {humanbytes(total)}**\n"
            "**│**\n"
            f"**├📦 Pʀᴏɢʀᴇꜱꜱ : {percentage:.2f}%**\n"
            "**│**\n"
            f"**├🚀 Sᴘᴇᴇᴅ : {speed:.2f} 𝙼𝙱/s**\n"
            "**│**\n"
            f"**├⏱️ Eᴛᴀ : {eta_min}𝚖𝚒𝚗, {eta_sec}𝚜𝚎𝚌**\n"
            "**│**\n"
            f"**├🏮 Cᴘᴜ : {cpu_usage}%  |  Rᴀᴍ : {ram_usage}%**\n"
            "**│**\n"
            f"**╰─[{progress_bar_str}]**"
        )

        await status_message.edit(text)

        if percentage >= 100:
            await status_message.edit("✅ **Fɪʟᴇ Dᴏᴡɴʟᴏᴀᴅ Cᴏᴍᴘʟᴇᴛᴇ!**\n**🎵 Aᴜᴅɪᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ...**")

    except Exception as e:
        print(f"Error updating progress: {e}")


async def update_progress(message, queue):
    """Updates progress bar while downloading."""
    last_update_time = [0]
    start_time = time.time()

    while True:
        data = await queue.get()
        if data is None:
            break

        if isinstance(data, dict):
            status = data.get("status")
            if status == "finished":
                await message.edit_text("✅ **Download Finished!**")
                break
            elif status == "error":
                await message.edit_text("❌ **Error occurred!**")
                break
        else:
            current, total, label = data
            current_label = label
            await progress_bar(current, total, message, start_time, last_update_time, current_label)


@Client.on_message(filters.regex(TERABOX_REGEX))
async def detect_terabox_link(client, message):
    match = re.search(TERABOX_REGEX, message.text)
    if not match:
        return  # No Terabox link found

    link = match.group(1)
    sent = await message.reply("Fetching file info...", quote=True)

    result = get_terabox_info(link)

    if "error" in result:
        await sent.edit(f"Error fetching file:\n`{result['error']}`")
        return

    title = result['title']
    size = result['size']
    download_url = result['download_url']
    thumbnail = result.get('thumbnail')  # 360x270 or None

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇️ Download", callback_data=download)]
    ])

    caption = f"**{title}**\n\n**Size:** {size}"

    if thumbnail:
        await sent.delete()
        await message.reply_photo(
            photo=thumbnail,
            caption=caption,
            reply_markup=btn,
            quote=True
        )
    else:
        await sent.edit(
            caption,
            reply_markup=btn,
            disable_web_page_preview=True
        )
        


@Client.on_callback_query(filters.regex(r'^download\|'))
async def handle_download_button(client, callback_query):
    chat_id = callback_query.message.chat.id
    tera_link = callback_query.message.reply_to_message.text
    await download_video(client, callback_query, chat_id, tera_link)
