from pyrogram import Client, filters
from pyrogram.types import Message
from requests_html import HTMLSession
import re

def mediafire(url, session=None):
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""
    if final_link := re.findall(
        r"https?:\/\/download\d+\.mediafire\.com\/\S+\/\S+\/\S+", url
    ):
        return final_link[0]

    def _repair_download(url, session):
        try:
            html = HTMLSession().get(url).text
            if new_link := re.findall(r'//a[@id="continue-btn"]/@href', html):
                return mediafire(f"https://mediafire.com/{new_link[0]}")
        except Exception as e:
            raise Exception(f"ERROR: {e.__class__.__name__}") from e

    if session is None:
        session = HTMLSession()
    try:
        html = session.get(url).text
    except Exception as e:
        session.close()
        raise Exception(f"ERROR: {e.__class__.__name__}") from e
    if error := re.findall(r'//p[@class="notranslate"]/text()', html):
        session.close()
        raise Exception(f"ERROR: {error[0]}")
    if re.findall("//div[@class='passwordPrompt']", html):
        if not _password:
            session.close()
            raise Exception(f"ERROR: Password required.")
        try:
            html = session.post(url, data={"downloadp": _password}).text
        except Exception as e:
            session.close()
            raise Exception(f"ERROR: {e.__class__.__name__}") from e
        if re.findall("//div[@class='passwordPrompt']", html):
            session.close()
            raise Exception("ERROR: Wrong password.")
    if not (final_link := re.findall('//a[@aria-label="Download file"]/@href', html)):
        if repair_link := re.findall("//a[@class='retry']/@href", html):
            return _repair_download(repair_link[0], session)
        raise Exception("ERROR: No links found. Try Again")
    if final_link[0].startswith("//"):
        final_url = f"https://{final_link[0][2:]}"
        if _password:
            final_url += f"::{_password}"
        return mediafire(final_url, session)
    session.close()
    return final_link[0]

app = Client
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
