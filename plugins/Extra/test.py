from pyrogram import Client, filters
from pyrogram.types import Message
import requests
from bs4 import BeautifulSoup
import re

app = Client
def extract_file_id(gdrive_url: str) -> str | None:
    # Match patterns like https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", gdrive_url)
    if match:
        return match.group(1)
    # Also support id=FILE_ID
    match = re.search(r"id=([a-zA-Z0-9_-]+)", gdrive_url)
    return match.group(1) if match else None

def get_confirmed_download_url(file_id: str) -> str | None:
    session = requests.Session()
    base_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = session.get(base_url)
    
    # Parse the confirmation token
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup.find_all("a"):
        href = tag.get("href", "")
        if "confirm=" in href:
            confirm_token = re.search(r"confirm=([a-zA-Z0-9_-]+)", href)
            if confirm_token:
                confirm = confirm_token.group(1)
                download_url = f"https://drive.google.com/uc?export=download&confirm={confirm}&id={file_id}"
                return download_url
    return None

@app.on_message(filters.command("extractlink") & filters.private)
async def extract_link_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Please send a Google Drive link with the command.\n\nExample:\n`/extractlink https://drive.google.com/file/d/FILE_ID/view?usp=sharing`")
        return

    url = message.command[1]
    file_id = extract_file_id(url)

    if not file_id:
        await message.reply_text("❌ Invalid Google Drive link.")
        return

    await message.reply_text("🔍 Extracting direct download link...")

    download_url = get_confirmed_download_url(file_id)

    if download_url:
        await message.reply_text(f"✅ Direct download link:\n`{download_url}`", disable_web_page_preview=True)
    else:
        await message.reply_text("⚠️ Failed to extract direct download link. Maybe the file is private or needs login.")
