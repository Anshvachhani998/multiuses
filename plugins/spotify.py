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

def im_human():
    time.sleep(random.uniform(1.0, 5.0))

def get_spotidown_link(song_url):
    options = uc.ChromeOptions()
    options.headless = True

    # ✅ FIX: correct binary location
    options.binary_location = "/usr/bin/google-chrome"

    # (Optional but recommended for headless on server)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options, use_subprocess=True)

    result = None

    try:
        driver.get('https://spotidown.app/')
        im_human()
        time.sleep(5)

        try:
            Try_to_consent = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    'body > div.fc-consent-root > div.fc-dialog-container > div.fc-dialog.fc-choice-dialog > div.fc-footer-buttons-container > div.fc-footer-buttons > button.fc-button.fc-cta-do-not-consent.fc-secondary-button'))
            )
            Try_to_consent.click()
        except TimeoutException:
            pass

        im_human()
        Url_textbox = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="url"]'))
        )
        Url_textbox.send_keys(song_url)

        Download_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#send'))
        )
        Download_button.click()
        im_human()

        Download_url = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="download-section"]/div/div/div[1]/div[3]/div[1]/a'))
        )
        result = Download_url.get_attribute('href')

    finally:
        driver.quit()

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


