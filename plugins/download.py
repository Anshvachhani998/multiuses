import os
import re
import time
import random
import string
import asyncio
import logging
from utils import convert_to_bytes
from yt_dlp import YoutubeDL
from plugins.progress_bar import yt_progress_hook, update_progress
from plugins.upload import upload_video

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


DOWNLOAD_DIR = "downloads"

async def download_video(client, chat_id, youtube_link):
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


    def run_pytubefix():
        nonlocal output_filename, caption, duration, width, height, youtube_thumbnail_url, thumbnail_path
        try:
            yt_dlp_options = {
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                'format': 'best',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [lambda d: yt_progress_hook(d, queue, client)]
            }

            with YoutubeDL(yt_dlp_options) as ydl:
                info = ydl.extract_info(youtube_link, download=True)
                caption = info.get('title', 'Untitled')
                filename = ydl.prepare_filename(info)
                filename_only = f"{caption}_{timestamp}-{random_str}.mp4"
                final_filename = os.path.join(DOWNLOAD_DIR, filename_only)

                # Rename file if necessary
                if os.path.exists(filename):
                    os.rename(filename, final_filename)
                    output_filename = final_filename
                else:
                    output_filename = filename

                youtube_thumbnail_url = info.get('thumbnail')
                duration = info.get('duration', 0)
                width = info.get('width', 640)
                height = info.get('height', 360)

                logging.info(f"Downloaded file: {output_filename}")
                asyncio.run_coroutine_threadsafe(queue.put({"status": "finished"}), client.loop)

        except Exception as e:
            logging.error(f"Download Error: {e}")
            asyncio.run_coroutine_threadsafe(queue.put({"status": "error", "message": str(e)}), client.loop)

    download_task = asyncio.create_task(asyncio.to_thread(run_pytubefix))
    progress_task = asyncio.create_task(update_progress(status_msg, queue))

    await download_task
    await progress_task

    if output_filename and os.path.exists(output_filename):
        await status_msg.edit_text("📤 **Preparing for upload...**")

        durations = 0
        logging.info(f'MSG test {status_msg}')
        await upload_video(client, chat_id, output_filename, caption, durations, width, height, status_msg, thumbnail_path, youtube_link)
    else:
        error_message = f"❌ **Download Failed!**\nOutput filename: {output_filename}\nFile exists: {os.path.exists(output_filename)}"
        logging.error(error_message)
        await status_msg.edit_text(error_message)
