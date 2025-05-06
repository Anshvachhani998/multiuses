from pyrogram import Client, filters
from pyrogram.types import Message
from requests_html import HTMLSession
import re

# Mediafire function to fetch download link
def mediafire(url, session=None):
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""

    # Look for an immediate download link
    if final_link := re.findall(
        r"https?:\/\/download\d+\.mediafire\.com\/\S+\/\S+\/\S+", url
    ):
        return final_link[0]

    def _repair_download(url, session):
        try:
            html = session.get(url).text
            # Looking for continue-btn
            if new_link := re.findall(r'//a[@id="continue-btn"]/@href', html):
                return mediafire(f"https://mediafire.com/{new_link[0]}", session)
        except Exception as e:
            raise Exception(f"ERROR: {e.__class__.__name__}") from e

    if session is None:
        session = HTMLSession()
    
    try:
        html = session.get(url).text
    except Exception as e:
        session.close()
        raise Exception(f"ERROR: {e.__class__.__name__}") from e
    
    # Check for error messages on the page
    if error := re.findall(r'//p[@class="notranslate"]/text()', html):
        session.close()
        raise Exception(f"ERROR: {error[0]}")
    
    # Password protection
    if re.findall("//div[@class='passwordPrompt']", html):
        if not _password:
            session.close()
            raise Exception("ERROR: Password required.")
        try:
            html = session.post(url, data={"downloadp": _password}).text
        except Exception as e:
            session.close()
            raise Exception(f"ERROR: {e.__class__.__name__}") from e
        if re.findall("//div[@class='passwordPrompt']", html):
            session.close()
            raise Exception("ERROR: Wrong password.")
    
    # If no download link is found, check for retry options
    if not (final_link := re.findall('//a[@aria-label="Download file"]/@href', html)):
        if repair_link := re.findall("//a[@class='retry']/@href", html):
            return _repair_download(repair_link[0], session)
        session.close()
        raise Exception("ERROR: No links found. Try Again")

    # Process the final download link
    if final_link[0].startswith("//"):
        final_url = f"https://{final_link[0][2:]}"
        if _password:
            final_url += f"::{_password}"
        return mediafire(final_url, session)
    
    session.close()
    return final_link[0]

# Initialize the Pyrogram client
app = Client

# Command handler for '/mediafire' command
@app.on_message(filters.command("mediafire"))
async def mediafire_command(client, message):
    url = message.text.split(" ", 1)[-1]
    if not url:
        await message.reply("Please provide a Mediafire link.")
        return

    try:
        download_link = mediafire(url)
        await message.reply(f"Here's your download link: {download_link}")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")


