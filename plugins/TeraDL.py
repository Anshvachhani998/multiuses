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
from database.db import db

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


async def get_video_duration(file_path):
    try:
        process = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await process.communicate()
        return int(float(stdout.decode().strip()))
    except Exception as e:
        print("Duration fetch error:", e)
        return 0
        
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

def generate_thumbnail_path():
    timestamp = int(time.time())
    unique_id = uuid.uuid4().hex
    return os.path.join("downloads", f"thumb_{unique_id}_{timestamp}.jpg")

async def download_and_resize_thumbnail(url):
    save_path = generate_thumbnail_path()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(save_path, 'wb') as f:
                        await f.write(await resp.read())
                else:
                    return None

        def resize():
            img = Image.open(save_path).convert("RGB")
            img.save(save_path, "JPEG", quality=85)

        await asyncio.to_thread(resize)
        return save_path

    except Exception as e:
        logging.exception("Thumbnail download failed: %s", e)
        return None

MAX_TG_FILE_SIZE = 2097152000  # 2GB (Telegram limit)

async def run_ffmpeg_async(cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(f"FFmpeg failed: {stderr.decode()}")
    return stdout, stderr

async def split_video(output_filename, max_size=MAX_TG_FILE_SIZE):
    file_size = os.path.getsize(output_filename)
    if file_size <= max_size:
        return [output_filename]  # No need to split

    duration = float(ffmpeg.probe(output_filename)["format"]["duration"])
    duration = int(duration)
    parts = ceil(file_size / max_size)
    split_duration = duration // parts
    base_name = os.path.splitext(output_filename)[0]

    split_files = []

    for i in range(parts):
        part_file = f"{base_name}_part{i+1}.mp4"
        start_time = i * split_duration

        cmd = [
            "ffmpeg",
            "-y",
            "-i", output_filename,
            "-ss", str(start_time),
            "-t", str(split_duration),
            "-c", "copy",
            part_file
        ]

        await run_ffmpeg_async(cmd)
        split_files.append(part_file)

    return split_files

async def upload_video(client, chat_id, output_filename, caption, duration, width, height, status_msg, terabox_link, thumbnail_path):
    if output_filename and os.path.exists(output_filename):
        await status_msg.edit_text("📤 **Uploading video...**")
        start_time = time.time()

        async def upload_progress(sent, total):
            await progress_for_pyrogram(sent, total, "📤 **Uploading...**", status_msg, start_time)

        try:
            split_files = await split_video(output_filename)
            total_parts = len(split_files)
            user = await client.get_users(chat_id)
            mention_user = f"[{user.first_name}](tg://user?id={user.id})"

            for idx, part_file in enumerate(split_files, start=1):
                part_caption = f"**{caption}**\n**Part {idx}/{total_parts}**" if total_parts > 1 else f"**{caption}**"
                
                with open(part_file, "rb") as video_file:
                    sent_message = await client.send_video(
                        chat_id=chat_id,
                        video=video_file,
                        progress=upload_progress,
                        caption=part_caption,
                        duration=duration // total_parts if total_parts > 1 else duration,
                        supports_streaming=True,
                        height=height,
                        width=width,
                        disable_notification=True,
                        thumb=thumbnail_path if thumbnail_path else None,
                        file_name=os.path.basename(part_file),                        
                    )

                formatted_caption = (
                    f"{part_caption}\n\n"
                    f"✅ **Dᴏᴡɴʟᴏᴀᴅᴇᴅ Bʏ: {mention_user}**\n"
                    f"📌 **Sᴏᴜʀᴄᴇ URL: [Click Here]({youtube_link})**"
                )
                await client.send_video(
                    chat_id=DUMP_CHANNEL,
                    video=sent_message.video.file_id,
                    caption=formatted_caption,
                    duration=duration // total_parts if total_parts > 1 else duration,
                    supports_streaming=True,
                    height=height,
                    width=width,
                    disable_notification=True,
                    thumb=thumbnail_path if thumbnail_path else None,
                    file_name=os.path.basename(part_file)
                )

                os.remove(part_file)

            await status_msg.edit_text("✅ **Upload Successful!**")
            await db.increment_task(chat_id)
            await db.increment_download_count()
            await status_msg.delete()

        except Exception as e:
            user = await client.get_users(chat_id)
            error_report = (
                f"❌ **Upload Failed!**\n\n"
                f"**User:** [{user.first_name}](tg://user?id={user.id}) (`{user.id}`)\n"
                f"**Filename:** `{output_filename}`\n"
                f"**Source:** [YouTube Link]({youtube_link})\n"
                f"**Error:** `{str(e)}`"
            )
            await client.send_message(LOG_CHANNEL, error_report)
            await status_msg.edit_text("❌ **Oops! Something went wrong during upload.**")

        finally:
            if os.path.exists(output_filename):
                os.remove(output_filename)
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            

    else:
        try:
            user = await client.get_users(chat_id)
            error_report = (
                f"❌ **Upload Failed - File Not Found!**\n\n"
                f"**User:** [{user.first_name}](tg://user?id={user.id}) (`{user.id}`)\n"
                f"**Expected File:** `{output_filename}`\n"
                f"**Source:** [YouTube Link]({youtube_link})"
            )
            await client.send_message(LOG_CHANNEL, error_report)
        except Exception as e:
            await client.send_message(LOG_CHANNEL, f"❌ Error while logging failed upload:\n`{str(e)}`")

        await status_msg.edit_text("❌ **Oops! Upload failed. Please try again later.**")


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

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start

    if current == total or round(diff % 5.00) == 0:
        percentage = (current / total) * 100
        speed = current / diff if diff > 0 else 0
        estimated_total_time = TimeFormatter(milliseconds=(total - current) / speed * 1000) if speed > 0 else "∞"

        # CPU & RAM Usage
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        # Progress Bar
        progress_bar = "■" + "■" * math.floor(percentage / 5) + "□" * (20 - math.floor(percentage / 5))

        text = (
            f"**╭───────Uᴘʟᴏᴀᴅɪɴɢ───────〄**\n"
            f"**│**\n"
            f"**├📁 Sɪᴢᴇ : {humanbytes(current)} ✗ {humanbytes(total)}**\n"
            f"**│**\n"
            f"**├📦 Pʀᴏɢʀᴇꜱꜱ : {round(percentage, 2)}%**\n"
            f"**│**\n"
            f"**├🚀 Sᴘᴇᴇᴅ : {humanbytes(speed)}/s**\n"
            f"**│**\n"
            f"**├⏱️ Eᴛᴀ : {estimated_total_time}**\n"
            f"**│**\n"
            f"**├🏮 Cᴘᴜ : {cpu_usage}%  |  Rᴀᴍ : {ram_usage}%**\n"
            f"**│**\n"
            f"**╰─[{progress_bar}]**"
        )

        try:
            await message.edit(text=text)
        except:
            pass

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

    result = await get_terabox_info(link)

    if "error" in result:
        await sent.edit(f"Error fetching file:\n`{result['error']}`")
        return

    title = result['title']
    size = result['size']
    download_url = result['download_url']
    thumbnail = result.get('thumbnail')  # 360x270 or None

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇️ Download", callback_data="download")]
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
        

@Client.on_callback_query(filters.regex(r'^download'))
async def handle_download_button(client, callback_query):
    chat_id = callback_query.message.chat.id
    teralink = callback_query.message.reply_to_message.text
    await download_video(client, callback_query, chat_id, teralink)



async def download_video(client, callback_query, chat_id, teralink):
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

    if output_filename and os.path.exists(output_filename):
        await status_msg.edit_text("📤 **Preparing for upload...**")
        thumbnail_file_id = await db.get_user_thumbnail(chat_id)
        if thumbnail_file_id:
            try:
                thumb_message = await client.download_media(thumbnail_file_id)
                thumbnail_path = thumb_message
            except Exception as e:
                logging.error(f"Thumbnail download error: {e}")

        if not thumbnail_path and youtube_thumbnail_url:
            thumbnail_path = await download_and_resize_thumbnail(youtube_thumbnail_url)
            
        durations = await get_video_duration(output_filename)
        
        await upload_video(
            client, chat_id, output_filename, caption,
            duration, width, height, status_msg, teralink, thumbnail_path
        )
    else:
        error_message = f"❌ **Download Failed!**\nOutput filename: {output_filename}\nFile exists: {os.path.exists(output_filename)}"
        logging.error(error_message)
        await status_msg.edit_text(error_message)
        
