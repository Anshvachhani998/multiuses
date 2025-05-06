from pyrogram import Client, filters
from pyrogram.types import Message
import requests
import re

# Initialize the bot
app = Client


# Extract Google Drive file ID from the URL
def extract_file_id(gdrive_url: str) -> str | None:
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", gdrive_url)
    if match:
        return match.group(1)
    match = re.search(r"id=([a-zA-Z0-9_-]+)", gdrive_url)
    return match.group(1) if match else None

# Get confirmed download URL with confirmation token
def get_confirmed_download_url(file_id: str) -> str:
    session = requests.Session()
    base_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = session.get(base_url, allow_redirects=True)

    # Check if confirmation page is encountered and extract the token
    if "confirm=" in response.url:
        confirm_token = re.search(r"confirm=([a-zA-Z0-9_-]+)", response.url)
        if confirm_token:
            confirm = confirm_token.group(1)
            # Return the confirmed URL with the token
            return f"https://drive.google.com/uc?export=download&confirm={confirm}&id={file_id}"

    # If no confirmation page, return the base URL (for public files)
    return base_url

# Command handler for /extractlink
@app.on_message(filters.command("extractlink") & filters.private)
async def extract_link_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text(
            "Please send a Google Drive link with the command.\n\nExample:\n"
            "`/extractlink https://drive.google.com/file/d/FILE_ID/view?usp=sharing`"
        )
        return

    url = message.command[1]
    file_id = extract_file_id(url)

    if not file_id:
        await message.reply_text("❌ Invalid Google Drive link.")
        return

    await message.reply_text("🔍 Extracting direct download link...")

    try:
        # Get the confirmed download URL (bypass the virus warning page)
        download_url = get_confirmed_download_url(file_id)

        # Test if the link is actually downloadable (status code 200 means it's valid)
        test_response = requests.head(download_url, allow_redirects=True)
        if test_response.status_code == 200:
            await message.reply_text(
                f"✅ Direct download link:\n`{download_url}`",
                disable_web_page_preview=True
            )
        else:
            await message.reply_text("⚠️ The link may be private or not downloadable.")
    except Exception as e:
        await message.reply_text(f"❌ Error occurred: `{e}`")

