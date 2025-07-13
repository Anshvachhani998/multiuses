import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import random
from pyrogram import Client, filters
import re



bot = Client



from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

import time

def im_human():
    time.sleep(1.5)

def get_spotidown_link(song_url):
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.binary_location = "/opt/google/chrome/chrome"
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    print("[INFO] Launching Chrome driver...")
    driver = uc.Chrome(
        options=options,
        use_subprocess=True,
        browser_executable_path="/opt/google/chrome/chrome"
    )

    result = None
    try:
        print("[INFO] Opening spotidown.app...")
        driver.get('https://spotidown.app/')
        WebDriverWait(driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        print("[INFO] Page loaded.")
        im_human()

        try:
            print("[INFO] Checking for consent...")
            consent = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.fc-button.fc-cta-do-not-consent'))
            )
            consent.click()
            print("[INFO] Consent clicked.")
        except TimeoutException:
            print("[INFO] No consent dialog.")

        im_human()

        print("[INFO] Typing URL...")
        url_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="url"]'))
        )
        url_box.clear()
        url_box.send_keys(song_url)

        print("[INFO] Clicking Download...")
        download_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#send'))
        )
        download_btn.click()
        im_human()

        print("[INFO] Waiting for any download link...")

        # 🟢 New logic: wait for any <a> inside download-section
        download_link = WebDriverWait(driver, 40).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@id="download-section"]//a[contains(@href,"http")]')
            )
        )
        result = download_link.get_attribute("href")
        print("[SUCCESS] Found download link:", result)

    except TimeoutException:
        print("[ERROR] Timed out.")
    except Exception as e:
        print("[ERROR]", str(e))
    finally:
        driver.quit()
        print("[INFO] Driver closed.")

    return result

# ✅ Ye sirf Spotify track/playlist URL pe chalega
SPOTIFY_LINK_REGEX = r"(https?://open\.spotify\.com/(track|playlist)/[a-zA-Z0-9]+)"

@bot.on_message(filters.regex(SPOTIFY_LINK_REGEX))
async def handle_spotify_link(_, message):
    song_url = message.text.strip()
    await message.reply("⏳ Processing your Spotify link...")

    try:
        link = get_spotidown_link(song_url)
        if link:
            await message.reply(f"✅ **Here is your download link:**\n{link}")
        else:
            await message.reply("❌ Sorry! Could not fetch the download link.")
    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")

# ✅ Agar koi valid link nahi hai to:
@bot.on_message(filters.text & ~filters.regex(SPOTIFY_LINK_REGEX))
async def handle_invalid(_, message):
    await message.reply("❌ Please send a valid **Spotify track or playlist URL** only!")


