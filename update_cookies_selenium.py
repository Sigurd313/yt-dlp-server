import time
from selenium import webdriver
import undetected_chromedriver as uc
from http.cookiejar import MozillaCookieJar

COOKIES_TXT = "cookies.txt"
PROFILE_DIR = "selenium-profile"

def save_cookies(driver, path):
    cj = MozillaCookieJar(path)
    for cookie in driver.get_cookies():
        c = {
            "version": 0,
            "name": cookie["name"],
            "value": cookie["value"],
            "port": None,
            "domain": cookie["domain"],
            "path": cookie["path"],
            "secure": cookie.get("secure", False),
            "expires": cookie.get("expiry"),
            "discard": False,
            "comment": None,
            "comment_url": None,
            "rest": {},
            "rfc2109": False,
        }
        cj.set_cookie(cj._cookie_from_cookie_tuple((c["name"], c["value"], c["domain"], c["path"])))
    cj.save(ignore_discard=True, ignore_expires=True)

options = uc.ChromeOptions()
options.user_data_dir = PROFILE_DIR
options.add_argument("--headless=new")
options.binary_location = "/usr/bin/chromium"

driver = uc.Chrome(options=options, headless=True)

try:
    driver.get("https://www.youtube.com")
    time.sleep(5)
    save_cookies(driver, COOKIES_TXT)
    print("✅ cookies.txt сохранён!")
finally:
    driver.quit()
