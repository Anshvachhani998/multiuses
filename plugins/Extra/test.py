from pyrogram import Client, filters
from pyrogram.types import Message
from requests_html import HTMLSession
import re

# Mediafire function to fetch download link
from requests_html import HTMLSession

def mediafire(url, session=None):
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""

    if final_link := re.findall(r"https?:\/\/download\d+\.mediafire\.com\/\S+\/\S+\/\S+", url):
        return final_link[0]

    if session is None:
        session = HTMLSession()

    try:
        html = session.get(url)
        html.render()  # Render JavaScript content
        html_content = html.html  # Get rendered HTML
    except Exception as e:
        session.close()
        raise Exception(f"ERROR: {e.__class__.__name__}") from e

    print(html_content)  # Debugging line to inspect the rendered HTML

    # Continue with your existing parsing logic here
    # Example:
    if not (final_link := re.findall('//a[@aria-label="Download file"]/@href', html_content)):
        raise Exception("ERROR: No links found. Try Again")
    
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


