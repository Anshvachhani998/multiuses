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

from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

def im_human():
    time.sleep(1.5)  # Simulate human-like pause

def get_spotidown_link(song_url):
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")  # Headless Chrome 109+ style
    options.binary_location = "/opt/google/chrome/chrome"  # actual chrome binary
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # options.add_argument("--remote-debugging-port=9222")  # optional, uncomment if needed

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
        time.sleep(3)

        try:
            print("[INFO] Checking for consent dialog...")
            Try_to_consent = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    'body > div.fc-consent-root > div.fc-dialog-container > div.fc-dialog.fc-choice-dialog > div.fc-footer-buttons-container > div.fc-footer-buttons > button.fc-button.fc-cta-do-not-consent.fc-secondary-button'))
            )
            Try_to_consent.click()
            print("[INFO] Consent dialog accepted.")
        except TimeoutException:
            print("[INFO] No consent dialog found, continuing...")

        im_human()

        print("[INFO] Locating URL textbox...")
        Url_textbox = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="url"]'))
        )
        print("[INFO] URL textbox found, sending URL.")
        Url_textbox.clear()
        Url_textbox.send_keys(song_url)

        print("[INFO] Locating Download button...")
        Download_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#send'))
        )
        print("[INFO] Clicking Download button.")
        Download_button.click()
        im_human()

        print("[INFO] Waiting for Download link...")
        Download_url = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="download-section"]/div/div/div[1]/div[3]/div[1]/a'))
        )
        result = Download_url.get_attribute('href')
        print("[SUCCESS] Download URL found:", result)

    except TimeoutException as e:
        print("[ERROR] Timeout while waiting for elements:", e)
    except NoSuchElementException as e:
        print("[ERROR] Element not found:", e)
    except WebDriverException as e:
        print("[ERROR] WebDriver exception:", e)
    except Exception as e:
        print("[ERROR] Unexpected error:", e)
    finally:
        print("[INFO] Quitting driver.")
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


