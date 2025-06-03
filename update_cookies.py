import asyncio
from playwright.async_api import async_playwright

NETSCAPE_HEADER = "# Netscape HTTP Cookie File\n"

def serialize_cookie(cookie):
    return "\t".join([
        cookie["domain"],
        "TRUE" if not cookie.get("hostOnly", False) else "FALSE",
        cookie["path"],
        "TRUE" if cookie.get("secure", False) else "FALSE",
        str(int(cookie.get("expires", 0))),
        cookie["name"],
        cookie["value"]
    ])

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.youtube.com", timeout=60000)

        cookies = await context.cookies()
        with open("cookies.txt", "w", encoding="utf-8") as f:
            f.write(NETSCAPE_HEADER)
            for cookie in cookies:
                # yt-dlp requires domain to start with a dot for cross-subdomain
                if not cookie["domain"].startswith("."):
                    cookie["domain"] = "." + cookie["domain"]
                f.write(serialize_cookie(cookie) + "\n")

        await browser.close()

asyncio.run(main())
