import json
import asyncio
from playwright.async_api import async_playwright

COOKIES_TXT_PATH = "cookies.txt"
AUTH_JSON_PATH = "auth.json"

def format_cookie_netscape(cookie):
    domain = cookie.get("domain", "")
    flag = "TRUE" if domain.startswith(".") else "FALSE"
    path = cookie.get("path", "/")
    secure = "TRUE" if cookie.get("secure") else "FALSE"
    expiry = cookie.get("expires", 1893456000)  # ~2030
    name = cookie["name"]
    value = cookie["value"]
    return f"{domain}\t{flag}\t{path}\t{secure}\t{int(expiry)}\t{name}\t{value}"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=AUTH_JSON_PATH)
        cookies = await context.cookies()
        netscape_lines = ["# Netscape HTTP Cookie File\n"] + [
            format_cookie_netscape(cookie) for cookie in cookies
        ]
        with open(COOKIES_TXT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(netscape_lines))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
