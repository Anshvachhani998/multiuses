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

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from googleapiclient.discovery import build
from plugins.download import download_video, aria2c_media, google_drive

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Directories
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Memory stores
memory_store = {}
rename_store = {}

# ========== Utility Functions ==========

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

@Client.on_message(filters.private & filters.reply)
async def rename_handscler(client, message):
    if message.reply_to_message and message.reply_to_message.text == "✏️ Please provide the new filename (including the extension). Reply to this message with the new filename.":
        chat_id = message.chat.id
        logger.info(f"User is replying to the correct prompt: {chat_id}")

        if chat_id in rename_store:
            random_id = rename_store.pop(chat_id)
            new_filename = message.text.strip()

            if not new_filename.endswith(('.mp4', '.mp3')):
                new_filename += '.mp4'  # Default to .mp4 if no extension

            logger.info(f"Received new filename: {new_filename} for random_id: {random_id}")

            memory_store[random_id]['filename'] = new_filename

            rename = await message.reply(f"✅ Filename changed to `{new_filename}`")

            entry = memory_store.pop(random_id)
            await start_download(client, chat_id, entry['link'], new_filename, entry['source'])
            await rename.delete()
        else:
            await message.reply("❌ You need to click 'Rename' first to change the filename.")
    else:
        logger.info(f"Message is not a valid reply: {message.text}")
        await message.reply("❌ You need to reply to the 'Rename' prompt with the new filename.")

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

def human_readable_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def clean_filename(filename, mime=None):
    name, ext = os.path.splitext(filename)
    if not ext or ext == '':
        if mime:
            guessed_ext = mimetypes.guess_extension(mime)
            ext = guessed_ext if guessed_ext else '.mkv'
        else:
            ext = '.mkv'
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    name = name.strip('_')

    return name + ext

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

async def is_supported_by_ytdlp(url):
    try:
        cmd = ["yt-dlp", "--quiet", "--simulate", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        return result.returncode == 0
    except Exception:
        return False


async def get_ytdlp_info(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        title = info.get('title', 'unknown_file')

        # Try to fetch filesize or approx filesize
        filesize = info.get('filesize') or info.get('filesize_approx')

        if not filesize:
            # Try fetching the size from formats if available
            for format in info.get('formats', []):
                if 'filesize' in format:
                    filesize = format['filesize']
                    break

        # Default to 0 if no size is found
        filesize = filesize or 0

        ext = info.get('ext', 'mp4')
        mime = f"video/{ext}"

    return title, filesize, mime

def extract_file_name_and_mime_magent(magnet_link):
    # Regex pattern to find the 'dn' parameter in the magnet link
    pattern = r"dn=([a-zA-Z0-9._%+-]+(?:[a-zA-Z0-9._%+-]*[a-zA-Z0-9])?)(?=&|$)"
    match = re.search(pattern, magnet_link)
    
    if match:
        # Extract the file name
        file_name = match.group(1)
        
        # Extract the file extension (e.g., .mkv, .mp4)
        file_extension = file_name.split('.')[-1]
        
        # Get MIME type based on file extension
        mime_type, _ = mimetypes.guess_type(file_name)
        
        # If MIME type couldn't be guessed, set it to a default
        if not mime_type:
            mime_type = "application/octet-stream"
        
        return file_name, mime_type
    else:
        return None, None
        
# ========== Main Handler ==========
@Client.on_message(filters.private & filters.text)
async def universal_handler(client, message):
    text = message.text.strip()

    if not (text.startswith("http") or text.startswith("magnet:") or text.endswith(".torrent")):
        return

    chat_id = message.chat.id
    random_id = str(chat_id) + "_" + str(message.id)

    checking_msg = await message.reply_text("🔎 Checking your link, please wait...")

    try:
        if "drive.google.com" in text:
            file_id = extract_file_id(text)
            if not file_id:
                await checking_msg.edit("❌ Invalid Google Drive link.")
                return

            # Processing message ko edit karo jab file info mile
            await checking_msg.edit("✅ Processing your Google Drive link...")

            name, size, mime = get_file_info(file_id)
 
            size_str = human_readable_size(size)
            clean_name = clean_filename(name, mime)

            memory_store[random_id] = {
                'link': text,
                'filename': clean_name,
                'source': 'gdrive'
            }

        elif "terabox.com" in text:
            await checking_msg.edit("✅ Processing your TeraBox link...")

            terabox_info = await get_terabox_info(text)
            logging.info(terabox_info)
            if "error" in terabox_info:
                await checking_msg.edit(f"❌ {terabox_info['error']}")
                return
                
            dwn = terabox_info.get("download_url")
            name, size, mime = await get_direct_file_info(dwn)
            size_str = human_readable_size(size)
            clean_name = clean_filename(name, mime)

            memory_store[random_id] = {
                'link': dwn,
                'filename': name,
                'source': 'terabox'
            }

        elif await is_supported_by_ytdlp(text):
            # Processing message ko edit karo jab file info mile
            await checking_msg.edit("✅ Processing your video link...")

            name, size, mime = await get_ytdlp_info(text)
            size_str = human_readable_size(size)
            clean_name = clean_filename(name, mime)

            memory_store[random_id] = {
                'link': text,
                'filename': clean_name,
                'source': 'yt-dlp'
            }

        elif "magnet:" in text:
            await checking_msg.edit("✅ Processing your video link...")

            name, mime = await extract_file_name_and_mime_magent(text)
            size_str = "Unkown"
            clean_name = clean_filename(name, mime)

            memory_store[random_id] = {
                'link': text,
                'filename': clean_name,
                'source': 'magnet'
            }
        else:
            name, size, mime = await get_direct_file_info(text)
            size_str = human_readable_size(size)
            clean_name = clean_filename(name, mime)

            await checking_msg.edit("✅ Processing your direct link...")

            memory_store[random_id] = {
                'link': text,
                'filename': clean_name,
                'source': 'direct'
            }

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Default Name", callback_data=f"default_{random_id}"), 
             InlineKeyboardButton("✏️ Rename", callback_data=f"rename_{random_id}")]
        ])
        await checking_msg.edit(
            f"📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`",
            reply_markup=buttons
        )

    except Exception as e:
        logging.error(f"Error processing link: {str(e)}")
        await checking_msg.edit("**This link is not accessible or not a direct download link.**")

                                 
@Client.on_callback_query()
async def button_handler(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id

    if data.startswith("default_"):
        random_id = data.split("_", 1)[1]
        await callback_query.message.delete()

        if random_id in memory_store:
            entry = memory_store.pop(random_id)
            await start_download(client, chat_id, entry['link'], entry['filename'], entry['source'])

    elif data.startswith("rename_"):
        random_id = data.split("_", 1)[1]
        if random_id in memory_store:

            entry = memory_store[random_id]
            filename = entry['filename']

            await callback_query.message.reply(
                f"✏️ **Send new name for this file:**\n\n"
                f"**📁 Current Filename:** `{filename}`",
                reply_markup=ForceReply(True)
            )

            rename_store[chat_id] = random_id

async def start_download(client, chat_id, link, filename, source):
    try:
        if source == "gdrive":
            await google_drive(client, chat_id, filename, link)
        elif source == "yt-dlp":
            await download_video(client, chat_id, filename, link)
        elif source == "direct":
            await aria2c_media(client, chat_id, link, filename)
        elif source == "terabox":
            await aria2c_media(client, chat_id, link, filename)
        elif source == "magnet":
            await aria2c_media(client, chat_id, link, filename)
    
    except Exception as e:
        await client.send_message(chat_id, f"❌ Download Error: {e}")
        logger.error(f"Download failed for {link}: {str(e)}")
