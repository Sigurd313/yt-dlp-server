import asyncio
from playwright.async_api import async_playwright

NETSCAPE_HEADER = "# Netscape HTTP Cookie File\n"

def serialize_cookie(cookie):
    return "\t".join([
        cookie["domain"],
        "TRUE" if cookie.get("hostOnly") is False else "FALSE",
        cookie["path"],
        "TRUE" if cookie.get("secure") else "FALSE",
        str(int(cookie["expires"])),
        cookie["name"],
        cookie["value"]
    ])

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # headless
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto("https://www.youtube.com", timeout=60000)

        print("✅ YouTube открыт, получаем cookies")

        cookies = await context.cookies()

        with open("cookies.txt", "w", encoding="utf-8") as f:
            f.write(NETSCAPE_HEADER)
            for cookie in cookies:
                f.write(serialize_cookie(cookie) + "\n")

        await browser.close()

asyncio.run(main())
