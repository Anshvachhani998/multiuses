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

        # Wait for main container (replace selector if needed)
        await page.wait_for_timeout(5000)

        # Scroll to bottom to force lazy-load images
        await page.evaluate(
            """() => {
                window.scrollBy(0, document.body.scrollHeight);
            }"""
        )
        await page.wait_for_timeout(5000)  # Wait after scroll

        html = await page.content()
        await browser.close()

        # Save for debug
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


@Client.on_message(filters.command("sendhtml"))
async def send_html(client, message):
    try:
        with open("hotstar_dump.html", "rb") as f:
            await message.reply_document(
                f,
                caption="📄 Here is the dumped Hotstar HTML file."
            )
    except FileNotFoundError:
        await message.reply("❌ File `hotstar_dump.html` not found. Run /hotstar first.")


@Client.on_message(filters.command("get")) 
async def get_hotstar_content(client, message):
    try:
        args = message.text.split(" ", 1)
        if len(args) < 2:
            await message.reply("❌ Please provide a URL!\nExample: `/get_content https://www.hotstar.com`")
            return
        
        url = args[1].strip()

        fetching_msg = await message.reply(f"⏳ Fetching content from:\n`{url}`")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=60000)

            await page.wait_for_selector("body", timeout=60000)


            full_content = await page.content()
            await browser.close()


        file_path = "page_content.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)
        await client.send_document(message.chat.id, file_path, caption=f"📄 Page Content from:\n`{url}`")
        os.remove(file_path)

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

