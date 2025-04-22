from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import re

def get_terabox_info(link):
    api_url = f"https://tera-dl.vercel.app/api?link={link}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

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

TERABOX_REGEX = r"(https?://(?:www\.)?(?:terabox\.com|d\.terabox\.(?:com|app)|(?:d|data)\.1024tera\.com|1024tera\.com|terafileshare\.com)[^\s]*)"

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
        [InlineKeyboardButton("⬇️ Download", url=download_url)]
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
        
