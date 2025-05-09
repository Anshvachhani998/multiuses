import os
import re
import asyncio
import logging
import uuid
import time
import mimetypes
import json
import subprocess
import aiohttp
import aiofiles
import requests
from bs4 import BeautifulSoup
import ffmpeg
from PIL import Image
from math import ceil
import pickle
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


MAX_TG_FILE_SIZE = 2097152000

active_tasks = {}
cancel_tasks = {}

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
    elif "T" in unit:
        return int(size * 1024 ** 4)
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


def ytdlp_clean(title: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = cleaned.replace(" ", "_")
    uid = uuid.uuid4().hex[:3]
    if not cleaned.lower().endswith(".mp4"):
        cleaned += f"_({uid}).mp4"
    return cleaned

def clean_filename(title: str, ext: str = None) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = cleaned.replace(" ", "_")
    original_ext = os.path.splitext(cleaned)[1]
    if not ext:
        ext = original_ext if original_ext else ".mkv"
    else:
        if not ext.startswith("."):
            ext = f".{ext}"
    base_name = cleaned
    if original_ext:
        base_name = cleaned[: -len(original_ext)]

    uid = uuid.uuid4().hex[:3]
    final_name = f"{base_name}_({uid}){ext}"

    return final_name

def clean_terabox(title: str, ext: str = None) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = cleaned.replace(" ", "_")
    original_ext = os.path.splitext(cleaned)[1]
    if not ext:
        ext = original_ext if original_ext else ".mkv"
    else:
        if not ext.startswith("."):
            ext = f".{ext}"
    base_name = cleaned
    if original_ext:
        base_name = cleaned[: -len(original_ext)]

    uid = uuid.uuid4().hex[:3]
    final_name = f"{base_name}_({uid}){ext}"

    return final_name
    
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



async def get_confirm_token_download_url(file_id):
    session = requests.Session()
    URL = f"https://drive.google.com/uc?export=download&id={file_id}"

    response = session.get(URL, stream=True)
    soup = BeautifulSoup(response.text, "html.parser")

    confirm_token = None
    for tag in soup.find_all("a"):
        href = tag.get("href")
        if href and "confirm=" in href:
            confirm_token = href.split("confirm=")[-1].split("&")[0]
            break

    if confirm_token:
        download_url = f"https://drive.google.com/uc?export=download&confirm={confirm_token}&id={file_id}"
    else:
        download_url = URL

    return download_url

async def get_ytdlp_info(url):
    try:
        command = ['yt-dlp', '-j', url]
        result = await asyncio.to_thread(subprocess.check_output, command)
        info_dict = json.loads(result.decode('utf-8'))
        title = info_dict.get("title", "Unknown Title")
        filesize = info_dict.get("filesize") or info_dict.get("filesize_approx")
        ext = info_dict.get("ext", "unknown")
        filesize = format_size(filesize) if filesize else "Unknown Size"
        mime = mimetypes.types_map.get(f".{ext}", "application/octet-stream")

        return {
            "title": title,
            "filesize": filesize,
            "mime": mime,
            "ext": ext
        }
    except Exception as e:
        print(f"[get_video_info] Error: {e}")
        return None

async def get_direct_file_info(url):
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.head(url, allow_redirects=True) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch file info. Status code: {response.status}")

                headers = response.headers
                filename = None
                if 'Content-Disposition' in headers:
                    dispo = headers['Content-Disposition']
                    filename_match = re.search(r'filename="?([^"]+)"?', dispo)
                    if filename_match:
                        filename = filename_match.group(1)

                size = int(headers.get('Content-Length', 0))
                mime = headers.get('Content-Type', None)
                if not filename:
                    filename = "downloaded_file"

                return filename, size, mime
    except asyncio.TimeoutError:
        raise Exception("Timeout exceeded while fetching file info.")
    except Exception as e:
        raise Exception(f"Error: {str(e)}")


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

