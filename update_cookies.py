import asyncio
from playwright.async_api import async_playwright
import json

YOUTUBE_URL = "https://www.youtube.com/"
COOKIES_PATH = "cookies.txt"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Без UI, работает на GitHub Actions
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(YOUTUBE_URL)
        print("Войдите в свой Google аккаунт вручную...")

        # Ждём подтверждения входа
        await page.wait_for_timeout(60000)  # ждём 60 секунд, или используйте кнопку на экране

        cookies = await context.cookies()
        with open(COOKIES_PATH, "w") as f:
            for cookie in cookies:
                cookie_line = "\t".join([
                    cookie.get("domain", ""),
                    "TRUE" if cookie.get("secure", False) else "FALSE",
                    cookie.get("path", "/"),
                    str(cookie.get("expires", 0)),
                    cookie.get("name", ""),
                    cookie.get("value", "")
                ])
                f.write(cookie_line + "\n")

        print("Cookies saved successfully.")
        await browser.close()

asyncio.run(run())
