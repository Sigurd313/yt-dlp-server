import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
import http.cookiejar as cookielib

COOKIES_TXT = "cookies.txt"
PROFILE_PATH = "selenium-profile"

def save_cookies(driver, path):
    cj = cookielib.MozillaCookieJar()
    for cookie in driver.get_cookies():
        c = cookielib.Cookie(
            version=0,
            name=cookie['name'],
            value=cookie['value'],
            port=None,
            port_specified=False,
            domain=cookie.get('domain', ''),
            domain_specified=bool(cookie.get('domain')),
            domain_initial_dot=cookie.get('domain', '').startswith('.'),
            path=cookie.get('path', '/'),
            path_specified=True,
            secure=cookie.get('secure', False),
            expires=cookie.get('expiry'),
            discard=False,
            comment=None,
            comment_url=None,
            rest={}
        )
        cj.set_cookie(c)
    cj.save(path, ignore_discard=True)
    print("✅ cookies.txt сохранён!")

if __name__ == "__main__":
    print("➡️ Запускаю браузер в headless-режиме...")

    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options, headless=True)
    driver.get("https://www.youtube.com")
    time.sleep(5)

    save_cookies(driver, COOKIES_TXT)
    driver.quit()

