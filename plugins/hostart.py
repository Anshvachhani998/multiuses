from pyrogram import Client, filters
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

HOTSTAR_URL = "https://www.hotstar.com/in/browse/reco-editorial/latest-releases/tp-ed_CJE3EAEaAQI"

@Client.on_message(filters.command("hotstar"))
async def hotstar_latest(_, message):
    await message.reply("🔍 Fetching latest Hotstar uploads...")

    try:
        shows = await fetch_latest()

        if not shows:
            await message.reply("❌ No shows found.")
            return

        text = "**🔥 Latest Hotstar Releases:**\n\n"
        for show in shows[:10]:
            text += f"🎬 [{show['title']}]({show['url']})\n"

        await message.reply(text, disable_web_page_preview=True)

    except Exception as e:
        await message.reply(f"❌ Error: {e}")


async def fetch_latest():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(HOTSTAR_URL)
        await page.wait_for_timeout(8000)

        html = await page.content()
        await browser.close()

        soup = BeautifulSoup(html, "html.parser")
        shows = []

        for tag in soup.find_all('a', href=True):
            title = tag.get("aria-label")
            href = tag["href"]
            if title and href.startswith("/in/"):
                shows.append({
                    "title": title.strip(),
                    "url": "https://www.hotstar.com" + href
                })

        return shows
