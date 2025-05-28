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
        await page.wait_for_selector('img')  # Wait until at least one image loads

        html = await page.content()
        await browser.close()

        # Debug step to verify HTML content
        with open("hotstar_dump.html", "w", encoding="utf-8") as f:
            f.write(html)

        soup = BeautifulSoup(html, "html.parser")
        shows = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if not href.startswith("/in/"):
                continue

            img_tag = a_tag.find('img')
            if img_tag and img_tag.has_attr('alt'):
                title = img_tag['alt'].strip()

                # High-quality image logic
                thumbnail = ""
                if img_tag.has_attr('srcset'):
                    srcset_parts = img_tag['srcset'].split(",")
                    if srcset_parts:
                        thumbnail = srcset_parts[-1].split()[0].strip()
                elif img_tag.has_attr('src'):
                    thumbnail = img_tag['src']

                if title:
                    shows.append({
                        "title": title,
                        "url": "https://www.hotstar.com" + href,
                        "thumbnail": thumbnail
                    })

        # Deduplicate
        unique_shows = []
        seen_titles = set()
        for show in shows:
            if show['title'] not in seen_titles:
                unique_shows.append(show)
                seen_titles.add(show['title'])

        return unique_shows
