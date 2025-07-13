import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.headless = False  # Disable headless for debug

driver = uc.Chrome(options=options)
driver.get('https://www.google.com')
print(driver.title)
driver.quit()
