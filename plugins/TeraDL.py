from pyrogram import Client, filters
import requests

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
            "download_url": info.get("Direct Download Link")
        }

    except Exception as e:
        return {"error": str(e)}

      

@Client.on_message(filters.command("terabox"))
async def terabox_handler(client, message):
    if len(message.command) < 2:
        await message.reply("Please provide a Terabox link.\nUsage: `/terabox <link>`", quote=True)
        return

    link = message.command[1]
    result = get_terabox_info(link)

    if "error" in result:
        await message.reply(f"API Error:\n`{result['error']}`", quote=True)
    else:
        reply_text = (
            f"**Title:** {result['title']}\n"
            f"[Download Link]({result['url']})"
        )
        await message.reply(reply_text, quote=True, disable_web_page_preview=True)
      
