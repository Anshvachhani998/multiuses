import os
import asyncio
import logging
from math import ceil
import ffmpeg 
from PIL import Image
import uuid
import time
import math
import ffmpeg
import aiohttp
import aiofiles

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


MAX_TG_FILE_SIZE = 2097152000

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
        logging.info("Duration fetch error:", e)
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
    try:
        size = float(size)
    except:
        return "0 B"

    if size <= 0:
        return "0 B"
    power = 1024
    n = 0
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    while size >= power and n < len(units) - 1:
        size /= power
        n += 1
    return f"{size:.2f} {units[n]}"

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
        
    
async def extract_fixed_thumbnail(video_path):
    base_name = os.path.splitext(video_path)[0]
    thumb_path = f"{base_name}_screenshot.jpg"

    def generate_thumb():
        try:
            (
                ffmpeg
                .input(video_path, ss=3)
                .filter('scale', 320, -1)
                .output(thumb_path, vframes=1)
                .run(quiet=True, overwrite_output=True)
            )
            return thumb_path
        except Exception as e:
            print(f"❌ Error generating thumbnail: {e}")
            return None

    return await asyncio.to_thread(generate_thumb)


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
        logging.info("Duration fetch error:", e)
        return 0
