import os
import uuid
import shutil
import uuid
import gdown
import re
import time
import random
import string
import asyncio
import logging
import subprocess
from utils import convert_to_bytes, download_and_resize_thumbnail, get_video_duration, extract_fixed_thumbnail, get_confirm_token_download_url, active_tasks, cancel_tasks
from yt_dlp import YoutubeDL
from database.db import db
from plugins.progress_bar import yt_progress_hook, update_progress
from plugins.upload import upload_media
from info import LOG_CHANNEL
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
 
async def download_video(client, chat_id, youtube_link, check):
    active_tasks[chat_id] = True
    await check.delete()
    status_msg = await client.send_message(chat_id, "⏳ **Starting Download...**")

    queue = asyncio.Queue()
    output_filename = None
    caption = ""
    duration = 0
    width, height = 640, 360
    thumbnail_path = None
    youtube_thumbnail_url = None

    timestamp = time.strftime("%y%m%d")
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))

    cancel_event = asyncio.Event()  # Create a cancellation event for this download
    cancel_tasks[chat_id] = cancel_event  # Store the event for this user

    def run_pytubefix():
        nonlocal output_filename, caption, duration, width, height, youtube_thumbnail_url, thumbnail_path
        try:
            yt_dlp_options = {
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s_{timestamp}-{random_str}.%(ext)s',
                'format': 'best',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [lambda d: yt_progress_hook(d, queue, client)]
            }

            with YoutubeDL(yt_dlp_options) as ydl:
                info = ydl.extract_info(youtube_link, download=True)
                if info.get('_type') == 'playlist' and 'entries' in info:
                    info = info['entries'][0]
                caption = info.get('title', 'Untitled')
                filename = ydl.prepare_filename(info)
                filename_only = f"{caption}_{timestamp}-{random_str}.mp4"
                final_filename = os.path.join(DOWNLOAD_DIR, filename_only)

                output_filename = filename
                logging.info(f"Video info: {info}///{output_filename}")

                youtube_thumbnail_url = info.get('thumbnail')
                duration = info.get('duration', 0)
                width = info.get('width', 640)
                height = info.get('height', 360)

                logging.info(f"Downloaded file: {output_filename}")

                if cancel_event.is_set():
                    asyncio.run_coroutine_threadsafe(status_msg.edit_text("❌ **Download Cancelled!**"), client.loop)
                    return

                asyncio.run_coroutine_threadsafe(queue.put({"status": "finished"}), client.loop)

        except Exception as e:
            if cancel_event.is_set():
            logging.info("Download cancelled")
            return
         
            if 'Download cancelled' not in str(e):
                error_message = (
                    "⚠️ **Oops! Something went wrong while fetching the formats. Please try again later.**\n\n"
                    "If the issue persists, please ask for help in our support group.\n\n"
                    "💬 Support Group: [SUPPORT](https://t.me/AnSBotsSupports)"
                )
                asyncio.run_coroutine_threadsafe(status_msg.edit_text(error_message), client.loop)
                asyncio.run_coroutine_threadsafe(
                    client.send_message(
                        LOG_CHANNEL,
                        f"❌ Exception in download with YTDLP:\n`{str(e)}`\n\nLink: {youtube_link}",
                        disable_web_page_preview=True
                    ),
                    client.loop
                )
            active_tasks.pop(chat_id, None)
            asyncio.run_coroutine_threadsafe(queue.put({"status": "error", "message": str(e)}), client.loop)

    download_task = asyncio.create_task(asyncio.to_thread(run_pytubefix))
    progress_task = asyncio.create_task(update_progress(status_msg, queue))

    await download_task
    await progress_task
    if output_filename and os.path.exists(output_filename):
        file_ext = os.path.splitext(output_filename)[1].lower()
        file_size = os.path.getsize(output_filename)
        if not file_ext in ['.mp4', '.mkv'] and file_size > 2 * 1024 * 1024 * 1024:
            await status_msg.edit_text("**Cannot upload ZIP/RAR/TAR files larger than 2GB.**")
            os.remove(output_filename)
            return
        await status_msg.edit_text("📤 **Preparing for upload...**")

        thumbnail_file_id = await db.get_user_thumbnail(chat_id)
        if thumbnail_file_id:
            try:
                thumb_message = await client.download_media(thumbnail_file_id)
                thumbnail_path = thumb_message
            except Exception as e:
                logging.error(f"Thumbnail download error: {e}")

        if not thumbnail_path and youtube_thumbnail_url:
            try:
                thumbnail_path = await download_and_resize_thumbnail(youtube_thumbnail_url)
            except Exception as e:
                logging.error(f"Error downloading/resizing YouTube thumbnail: {e}")

        if not thumbnail_path:
            try:
                thumbnail_path = await extract_fixed_thumbnail(output_filename)
            except Exception as e:
                logging.error(f"Error extracting fixed thumbnail: {e}")

        try:
             duration = await get_video_duration(output_filename)
        except Exception as e:
            duration = None

        asyncio.create_task(upload_media(client, chat_id, output_filename, caption, duration, width, height, status_msg, thumbnail_path, youtube_link))

    else:
        error_message = f"❌ **Download Failed!**"
        logging.error(error_message)
        active_tasks.pop(chat_id, None)
        await status_msg.edit_text(error_message)

def generate_unique_name(original_name):
    timestamp = time.strftime("%y%m%d")
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
    base, ext = os.path.splitext(original_name)
    return f"{base}_{timestamp}-{random_str}{ext}"

def aria2c_download(url, download_dir, label, queue, client, cancel_event):
    before_files = set(os.listdir(download_dir))

    cmd = [
        "aria2c",
        f"--dir={download_dir}",
        "--max-connection-per-server=16",
        "--split=16",
        "--min-split-size=1M",
        "--console-log-level=warn",
        "--summary-interval=1",
        "--enable-mmap=false",
        "--allow-overwrite=true",
        url
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            if cancel_event.is_set():
                process.terminate()
                return None, True  # Download cancelled by user

            print("ARIA2C >>", line.strip())

            match = re.search(r'(\d+(?:\.\d+)?)([KMG]?i?B)/(\d+(?:\.\d+)?)([KMG]?i?B)', line)
            if match:
                downloaded = convert_to_bytes(float(match.group(1)), match.group(2))
                total = convert_to_bytes(float(match.group(3)), match.group(4))

                asyncio.run_coroutine_threadsafe(
                    queue.put((downloaded, total, label)),
                    client.loop
                )

        process.wait()

        after_files = set(os.listdir(download_dir))
        new_files = list(after_files - before_files)

        if not new_files:
            return None, False  # No file found

        downloaded_file = os.path.join(download_dir, new_files[0])

        unique_name = generate_unique_name(new_files[0])
        final_path = os.path.join(download_dir, unique_name)
        os.rename(downloaded_file, final_path)

        return final_path, False  # Success, not cancelled

    except Exception as e:
        print("ARIA2C ERROR:", str(e))
        return None, False  # Error occurred


        
async def aria2c_media(client, chat_id, download_url, check):
    active_tasks[chat_id] = True
    await check.delete()
    status_msg = await client.send_message(chat_id, "⏳ **Starting Download...**")

    cancel_event = asyncio.Event()
    cancel_tasks[chat_id] = cancel_event
    queue = asyncio.Queue()
    output_filename = None
    caption = "Downloaded via aria2c"
    duration = 0
    width, height = 640, 360
    thumbnail_path = None
    error_occurred = False

    timestamp = time.strftime("%y%m%d")
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))

    async def run_aria():
        nonlocal output_filename, caption, width, height, thumbnail_path, error_occurred
        try:
            final_filenames, was_cancelled  = await asyncio.to_thread(
                aria2c_download,
                download_url,
                "downloads",
                caption,
                queue,
                client,
                cancel_event
            )
            if was_cancelled:
                await status_msg.edit("**Download Cancelled**")
                active_tasks.pop(chat_id, None)
                cancel_tasks.pop(chat_id, None)
                return
            
            output_filename = final_filenames
            caption = os.path.splitext(os.path.basename(output_filename))[0]
            asyncio.run_coroutine_threadsafe(queue.put({"status": "finished"}), client.loop)

        except Exception as e:
            error_occurred = True
            asyncio.run_coroutine_threadsafe(
                client.send_message(
                    LOG_CHANNEL,
                    f"Exception in download with ARIA2c:\n`{str(e)}`\n\nLink: {download_url}",
                    disable_web_page_preview=True
                ),
                client.loop
            )
            await queue.put({"status": "error", "message": str(e)})
            active_tasks.pop(chat_id, None)
            cancel_tasks.pop(chat_id, None)
            return

    download_task = asyncio.create_task(run_aria())
    progress_task = asyncio.create_task(update_progress(status_msg, queue))

    await download_task
    await progress_task

    if error_occurred:
        error_message = (
                "⚠️ **Oops! Something went wrong while fetching the formats. Please try again later.**\n\n"
                "If the issue persists, please ask for help in our support group.\n\n"
                "💬 Support Group: [SUPPORT](https://t.me/AnSBotsSupports)"
            )
        await status_msg.edit_text(error_message)
        return

    # Prepare for upload if no error occurred
    if output_filename and os.path.exists(output_filename):
        file_ext = os.path.splitext(output_filename)[1].lower()
        file_size = os.path.getsize(output_filename)
        if not file_ext in ['.mp4', '.mkv'] and file_size > 2 * 1024 * 1024 * 1024:
            await status_msg.edit_text("**Cannot upload ZIP/RAR/TAR files larger than 2GB.**")
            os.remove(output_filename)
            return
        await status_msg.edit_text("📤 **Preparing for upload...**")

        # Get user thumbnail
        thumbnail_file_id = await db.get_user_thumbnail(chat_id)
        if thumbnail_file_id:
            try:
                thumb_message = await client.download_media(thumbnail_file_id)
                thumbnail_path = thumb_message
            except Exception as e:
                logging.error(f"Thumbnail download error: {e}")

        # Extract from video if no thumbnail
        if not thumbnail_path:
            try:
                thumbnail_path = await extract_fixed_thumbnail(output_filename)
            except Exception as e:
                logging.error(f"Error extracting fixed thumbnail: {e}")

        # Get video duration
        try:
            duration = await get_video_duration(output_filename)
        except Exception as e:
            logging.error(f"Error fetching video metadata: {e}")
            duration = None

        asyncio.create_task(upload_media(
            client,
            chat_id,
            output_filename,
            caption,
            duration,
            width,
            height,
            status_msg,
            thumbnail_path,
            download_url
        ))
    else:
        active_tasks.pop(chat_id, None)
        cancel_tasks.pop(chat_id, None)
        await status_msg.edit_text("❌ **Download Failed!**")


async def google_drive(client, chat_id, gdrive_url, filename, check):
    active_tasks[chat_id] = True
    await check.delete()

    cancel_event = asyncio.Event()
    cancel_tasks[chat_id] = cancel_event

    status_msg = await client.send_message(chat_id, "⏳ **Starting Download...**")
 
    queue = asyncio.Queue()
    output_filename = None
    caption = "Downloading"
    duration = 0
    width, height = 640, 360
    thumbnail_path = None
    error_occurred = False

    async def run_gdrive():
        nonlocal output_filename, width, height, thumbnail_path, error_occurred, caption
        try:
            match = re.search(r"/d/([a-zA-Z0-9_-]+)", gdrive_url)
            if match:
                file_id = match.group(1)
            else:
                match = re.search(r"id=([a-zA-Z0-9_-]+)", gdrive_url)
                file_id = match.group(1) if match else None

            if not file_id:
                raise Exception("Invalid Google Drive URL")

            download_url = f"https://drive.google.com/uc?id={file_id}"

            logging.info(download_url)
            final_filenames, was_cancelled = await asyncio.to_thread(
                gdown_download,
                gdrive_url,
                "gdowns",
                filename,
                caption,
                queue,
                client,
                cancel_event
            )
            if was_cancelled:
                await status_msg.edit("**Download Cancelled**")
                active_tasks.pop(chat_id, None)
                cancel_tasks.pop(chat_id, None)
                return
            output_filename = final_filenames
            caption = os.path.splitext(os.path.basename(output_filename))[0]
            asyncio.run_coroutine_threadsafe(queue.put({"status": "finished"}), client.loop)

        except Exception as e:
            error_occurred = True
            await client.send_message(
                LOG_CHANNEL,
                f"❌ Exception in download:\n`{str(e)}`\n\nLink: {gdrive_url}",
                disable_web_page_preview=True
            )
            await queue.put({"status": "error", "message": str(e)})
            active_tasks.pop(chat_id, None)
            return

    download_task = asyncio.create_task(run_gdrive())
    progress_task = asyncio.create_task(update_progress(status_msg, queue))

    await download_task
    await progress_task

    if error_occurred:
        error_message = (
            "⚠️ **Oops! Something went wrong while downloading.**\n\n"
            "You can try again or ask for help.\n\n"
            "💬 Support Group: [SUPPORT](https://t.me/AnSBotsSupports)"
        )
        await status_msg.edit_text(error_message)
        cancel_tasks.pop(chat_id, None)
        return

    if output_filename and os.path.exists(output_filename):
        file_ext = os.path.splitext(output_filename)[1].lower()
        file_size = os.path.getsize(output_filename)
        if not file_ext in ['.mp4', '.mkv'] and file_size > 2 * 1024 * 1024 * 1024:
            await status_msg.edit_text("**Cannot upload ZIP/RAR/TAR files larger than 2GB.**")
            os.remove(output_filename)
            return

        await status_msg.edit_text("📤 **Preparing for upload...**")
        thumbnail_file_id = await db.get_user_thumbnail(chat_id)

        if thumbnail_file_id:
            try:
                thumb_message = await client.download_media(thumbnail_file_id)
                thumbnail_path = thumb_message
            except Exception as e:
                logging.error(f"Thumbnail download error: {e}")

        if not thumbnail_path:
            try:
                thumbnail_path = await extract_fixed_thumbnail(output_filename)
                logging.info(thumbnail_path)
            except Exception as e:
                logging.error(f"Error extracting fixed thumbnail: {e}")

        try:
            duration = await get_video_duration(output_filename)
        except Exception as e:
            logging.error(f"Error fetching video metadata: {e}")
            duration = None

        asyncio.create_task(upload_media(
            client, chat_id, output_filename, caption, duration,
            width, height, status_msg, thumbnail_path, gdrive_url
        ))

    else:
        await status_msg.edit_text("❌ **Download Failed!**")

    # Clean up
    active_tasks.pop(chat_id, None)
    cancel_tasks.pop(chat_id, None)


def gdown_download(url, download_dir, filename, label, queue, client, cancel_event):
    try:
        os.makedirs(download_dir, exist_ok=True)

        cmd = [
            "gdown",
            url,
            "--fuzzy",
            "--no-cookies",
            "--output", "gdowns/"
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            if cancel_event.is_set():
                process.terminate()
                return None, True  # Cancelled by user

            match = re.search(r'(\d+)%\|.*\| (\d+(\.\d+)?)([KMGT]?)\/(\d+(\.\d+)?)([KMGT]?)', line)
            if match:
                downloaded = convert_to_bytes(float(match.group(2)), match.group(4))
                total = convert_to_bytes(float(match.group(5)), match.group(7))

                asyncio.run_coroutine_threadsafe(
                    queue.put((downloaded, total, label)),
                    client.loop
                )
            else:
                print("No match found in line:", line.strip())

        process.wait()

        files = os.listdir(download_dir)
        if not files:
            return None, False  # No file found

        ffiles = [f for f in files if not f.startswith('.')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(download_dir, x)), reverse=True)
        original_path = os.path.join(download_dir, files[0])

        new_path = os.path.join(download_dir, filename)
        os.rename(original_path, new_path)

        return new_path, False  # Success, not cancelled

    except Exception as e:
        print("GDOWN ERROR:", str(e))
        return None, False  # Failed due to error


@Client.on_callback_query(filters.regex(r'^cancel_(\d+)$'))
async def cancel_download(client, callback_query):
    chat_id = int(callback_query.data.split("_")[1])
    if chat_id in cancel_tasks:
        cancel_tasks[chat_id].set()
        await callback_query.message.edit("**Download Cancelled!**")
        active_tasks.pop(chat_id, None)
        cancel_tasks.pop(chat_id, None)
    else:
        await callback_query.answer("No active download found.", show_alert=True)

