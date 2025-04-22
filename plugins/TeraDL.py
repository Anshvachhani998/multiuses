import os
import io
import re
import logging
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


import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def convert_to_bytes(size, unit):
    unit = unit.upper()
    if "K" in unit:
        return int(size * 1024)
    elif "M" in unit:
        return int(size * 1024 ** 2)
    elif "G" in unit:
        return int(size * 1024 ** 3)
    else:
        return int(size)


def format_size(size_in_bytes):
    """✅ File Size को KB, MB, या GB में Convert करता है"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024**2:
        return f"{round(size_in_bytes / 1024, 1)} KB"
    elif size_in_bytes < 1024**3:
        return f"{round(size_in_bytes / 1024**2, 1)} MB"
    else:
        return f"{round(size_in_bytes / 1024**3, 2)} GB"
        
def humanbytes(size):
    if not size:
        return "N/A"
    power = 2**10
    n = 0
    units = ["", "K", "M", "G", "T"]
    while size > power and n < len(units) - 1:
        size /= power
        n += 1
    return f"{round(size, 2)}{units[n]}B"

def TimeFormatter(milliseconds):
    seconds = milliseconds // 1000
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def manual_download_with_progress(url, output_path, label, queue, client):
    output_dir = os.path.dirname(output_path)
    output_file = os.path.basename(output_path)
    cmd = [
        "aria2c",
        f"--dir={output_dir}",
        f"--out={output_file}",
        "--max-connection-per-server=16",
        "--split=16",
        "--min-split-size=1M",
        "--console-log-level=warn",
        "--summary-interval=1",
        url
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        match = re.search(r'(\d+(?:\.\d+)?)([KMG]?i?B)/(\d+(?:\.\d+)?)([KMG]?i?B)', line)
        if match:
            downloaded = convert_to_bytes(float(match.group(1)), match.group(2))
            total = convert_to_bytes(float(match.group(3)), match.group(4))

            asyncio.run_coroutine_threadsafe(
                queue.put((downloaded, total, label)),
                client.loop
            )

    process.wait()
    

async def get_terabox_info(link):
    api_url = f"https://tera-dl.vercel.app/api?link={link}"
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
    teralink = callback_query.message.reply_to_message.text
    await download_video(client, callback_query, chat_id, teralink)



async def download_video(client, callback_query, chat_id, teralink):
    active_tasks[chat_id] = True
    status_msg = await client.send_message(chat_id, "⏳ **Starting Download...**")
    await callback_query.message.delete()

    queue = asyncio.Queue()
    output_filename = None
    caption = ""
    duration = 0
    width, height = 640, 360
    timestamp = time.strftime("%y%m%d")
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))

    async def run_terabox():
        nonlocal output_filename, caption, duration, width, height
        try:
            info = await get_terabox_info(teralink)

            if "error" in info:
                await status_msg.edit_text(f"❌ **Error:** {info['error']}")
                return

            caption = info.get("title") or "TeraBox File"
            download_url = info.get("download_url")
            file_ext = ".mp4" if ".mp4" in download_url else ".bin"
            filename_only = f"{caption}_{timestamp}-{random_str}{file_ext}"
            final_filename = os.path.join("downloads", filename_only)
            
            await asyncio.to_thread(manual_download_with_progress, download_url, final_filename, "📥 Downloading", queue, client)

            output_filename = final_filename
            await queue.put({"status": "finished"})

        except Exception as e:
            logging.error(f"Error: {e}")
            await queue.put({"status": "error", "message": str(e)})
            await status_msg.edit_text(f"❌ **Error:** {str(e)}")

    download_task = asyncio.create_task(run_terabox())
    progress_task = asyncio.create_task(update_progress(status_msg, queue))

    await download_task
    await progress_task

    # If the download is successful, prepare the file for upload
    if output_filename and os.path.exists(output_filename):
        await status_msg.edit_text("📤 **Preparing for upload...**")
        # Upload the video (assuming upload_video is defined elsewhere)
        await upload_video(
            client, chat_id, output_filename, caption,
            duration, width, height, status_msg, teralink
        )
    else:
        error_message = f"❌ **Download Failed!**\nOutput filename: {output_filename}\nFile exists: {os.path.exists(output_filename)}"
        logging.error(error_message)
        await status_msg.edit_text(error_message)
        
