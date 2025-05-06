from pyrogram import Client, filters
from pyrogram.types import Message
from requests_html import HTMLSession
import re

# Mediafire function to fetch download link
from requests_html import HTMLSession
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

import logging
from requests_html import HTMLSession
import re

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
        logger.INFO(f"Immediate download link found: {final_link[0]}")  # Log the found link
        return final_link[0]

    def _repair_download(url, session):
        try:
            html = session.get(url).text
            logger.INFO(f"Repair HTML content: {html}")  # Log the HTML content for debugging
            if new_link := re.findall(r'//a[@id="continue-btn"]/@href', html):
                logger.INFO(f"Found repair link: {new_link[0]}")  # Log the repair link
                return mediafire(f"https://mediafire.com/{new_link[0]}", session)
        except Exception as e:
            logger.error(f"ERROR in _repair_download: {e.__class__.__name__}")  # Log the error
            raise Exception(f"ERROR: {e.__class__.__name__}") from e

    if session is None:
        session = HTMLSession()

    try:
        html = session.get(url).text
        logger.INFO(f"Fetched HTML content: {html}")  # Log the HTML content after fetching
    except Exception as e:
        session.close()
        logger.error(f"Error fetching URL: {e.__class__.__name__}")  # Log the error
        raise Exception(f"ERROR: {e.__class__.__name__}") from e

    # Check for error messages on the page
    if error := re.findall(r'//p[@class="notranslate"]/text()', html):
        session.close()
        logger.error(f"Error found on page: {error[0]}")  # Log the error found on the page
        raise Exception(f"ERROR: {error[0]}")

    # Password protection
    if re.findall("//div[@class='passwordPrompt']", html):
        if not _password:
            session.close()
            logger.error("Password required.")  # Log if password is required
            raise Exception("ERROR: Password required.")
        try:
            html = session.post(url, data={"downloadp": _password}).text
            logger.INFO(f"HTML after password post: {html}")  # Log the HTML after posting the password
        except Exception as e:
            session.close()
            logger.error(f"Error posting password: {e.__class__.__name__}")  # Log the error
            raise Exception(f"ERROR: {e.__class__.__name__}") from e
        if re.findall("//div[@class='passwordPrompt']", html):
            session.close()
            logger.error("Wrong password.")  # Log if the password is incorrect
            raise Exception("ERROR: Wrong password.")

    # If no download link is found, check for retry options
    if not (final_link := re.findall('//a[@aria-label="Download file"]/@href', html)):
        if repair_link := re.findall("//a[@class='retry']/@href", html):
            logger.INFO(f"Found repair link: {repair_link[0]}")  # Log the repair link
            return _repair_download(repair_link[0], session)
        session.close()
        logger.error("No download link found.")  # Log when no download link is found
        raise Exception("ERROR: No links found. Try Again")

    # Process the final download link
    if final_link[0].startswith("//"):
        final_url = f"https://{final_link[0][2:]}"
        if _password:
            final_url += f"::{_password}"
        logger.INFO(f"Final download URL: {final_url}")  # Log the final URL
        return mediafire(final_url, session)

    session.close()
    logger.INFO(f"Final download URL: {final_link[0]}")  # Log the final link before returning
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


