import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.add_argument("--headless=new")  # headless mode explicitly
options.binary_location = "/opt/google/chrome/google-chrome"
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")

try:
    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.get("https://www.google.com")
    print("Title:", driver.title)
finally:
    driver.quit()
