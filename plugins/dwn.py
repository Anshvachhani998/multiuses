import sys
import os
import asyncio
import re
from yt_dlp import YoutubeDL
from pyrogram import Client, filters
from plugins.download import download_video, aria2c_media, google_drive
import mimetypes
import pickle
import re
from googleapiclient.discovery import build
from pyrogram import Client, filters
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Function to extract file ID from Google Drive link
def extract_file_id(link):
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',  # Pattern for /file/d/ID
        r'id=([a-zA-Z0-9_-]+)'        # Pattern for id=ID
    ]
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    return None

# Function to get file details from Google Drive using Google API
def get_file_info(file_id):
    creds = pickle.load(open("/app/plugins/token.pickle", "rb"))
    service = build("drive", "v3", credentials=creds)
    file = service.files().get(fileId=file_id, fields="name, size, mimeType").execute()
    name = file.get("name")
    size = int(file.get("size", 0))
    mime = file.get("mimeType")
    return name, size, mime

# Function to format file size into human-readable format
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

    # Clean the name
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    name = name.strip('_')

    return name + ext

import requests
from bs4 import BeautifulSoup

from cloudscraper import create_scraper
from lxml import html as HTML
from urllib.parse import urlparse
import re

from requests_html import HTMLSession
from urllib.parse import urlparse
import re

# Function to get the mediafire direct download link
def mediafire(url, session=None):
    if "/folder/" in url:
        return mediafireFolder(url)
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""
        
    if final_link := re.findall(r"https?:\/\/download\d+\.mediafire\.com\/\S+\/\S+\/\S+", url):
        return final_link[0]

    def _repair_download(url, session):
        try:
            html = HTML(session.get(url).text)
            if new_link := html.xpath('//a[@id="continue-btn"]/@href'):
                return mediafire(f"https://mediafire.com/{new_link[0]}")
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

    if session is None:
        session = HTMLSession()
        parsed_url = urlparse(url)
        url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    try:
        html = HTML(session.get(url).text)
    except Exception as e:
        session.close()
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

    if error := html.xpath('//p[@class="notranslate"]/text()'):
        session.close()
        raise DirectDownloadLinkException(f"ERROR: {error[0]}")

    if html.xpath("//div[@class='passwordPrompt']"):
        if not _password:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Password is required.")
        try:
            html = HTML(session.post(url, data={"downloadp": _password}).text)
        except Exception as e:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if html.xpath("//div[@class='passwordPrompt']"):
            session.close()
            raise DirectDownloadLinkException("ERROR: Wrong password.")

    if not (final_link := html.xpath('//a[@aria-label="Download file"]/@href')):
        if repair_link := html.xpath("//a[@class='retry']/@href"):
            return _repair_download(repair_link[0], session)
        raise DirectDownloadLinkException("ERROR: No links found in this page. Try again.")

    if final_link[0].startswith("//"):
        final_url = f"https://{final_link[0][2:]}"
        if _password:
            final_url += f"::{_password}"
        return mediafire(final_url, session)

    session.close()
    return final_link[0]

# Helper function for MediaFire downloading within your bot
async def mediafire_download(client, chat_id, url):
    try:
        # Try to get the MediaFire download link using the mediafire function
        download_link = mediafire(url)

        # Send the file download details
        file_name = download_link.split('/')[-1]  # Extract the file name
        info_message = f"📄 **File Name:** `{file_name}`\n🔗 [Download here]({download_link})"
        await client.send_message(chat_id, info_message)

    except DirectDownloadLinkException as e:
        await client.send_message(chat_id, f"❌ Error: {str(e)}")
    except Exception as e:
        await client.send_message(chat_id, f"❌ Error: {str(e)}")

# Main message handler for MediaFire links in the universal handler
@Client.on_message(filters.private & filters.text)
async def universal_handler(client, message):
    text = message.text.strip()

    if not text.startswith("http"):
        return

    chat_id = message.chat.id

    if "drive.google.com" in text:
        await message.reply("📥 Google Drive link detected! Fetching file details...")

        file_id = extract_file_id(text)
        if not file_id:
            return await message.reply("❌ Invalid Google Drive link.")

        try:
            name, size, mime = get_file_info(file_id)
            size_str = human_readable_size(size)
            clean_name = clean_filename(name, mime)

            info_message = f"📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`"
            await message.reply(info_message)

            await google_drive(client, chat_id, clean_name, text)

        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    elif "mediafire.com" in text:
        await message.reply("📥 MediaFire link detected! Fetching file details...")
        await mediafire_download(client, chat_id, text)

    else:
        await message.reply("📥 Checking link type...")

        try:
            if await is_supported_by_ytdlp(text):
                await message.reply("🔗 Supported by yt-dlp! Fetching details...")

                name, size, mime = await get_ytdlp_info(text)
                size_str = human_readable_size(size)
                clean_name = clean_filename(name, mime)

                info_message = f"📄 **File Name:** `{clean_name}`\n📦 **Size:** `{size_str}`\n🧾 **MIME Type:** `{mime}`"
                await message.reply(info_message)

                await download_video(client, chat_id, text)

            else:
                await message.reply("🔗 Direct link detected! Fetching details...")

                await download_video(client, chat_id, text)

        except Exception as e:
            await message.reply(f"❌ Error: {e}")


import subprocess
import re
import aiohttp

import aiohttp
import asyncio
import re


async def get_file_info(url):
    try:
        # Define a timeout
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True, timeout=timeout) as response:
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
        raise Exception("❌ Error: Timeout exceeded while fetching file info.")
    except Exception as e:
        raise Exception(f"❌ Error: {str(e)}")

import subprocess

async def is_supported_by_ytdlp(url):
    try:
        cmd = ["yt-dlp", "--quiet", "--simulate", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            return True
        else:
            return False

    except subprocess.TimeoutExpired:
        return False

    except Exception:
        return False

import yt_dlp

async def get_ytdlp_info(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'unknown_file')
        filesize = info.get('filesize') or info.get('filesize_approx') or 0
        ext = info.get('ext', 'mp4')
        mime = f"video/{ext}"

    return title, filesize, mime

