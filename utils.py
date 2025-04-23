import os
import asyncio
import logging
from math import ceil
import ffmpeg 

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


