import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.headless = False
options.binary_location = "/usr/bin/google-chrome"
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = uc.Chrome(options=options, use_subprocess=True)

driver.get("https://www.google.com")
print(driver.title)

driver.quit()
