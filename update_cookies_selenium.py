import undetected_chromedriver as uc
import time

URL = "https://www.youtube.com"
COOKIES_TXT = "cookies.txt"

def format_netscape_cookie(cookie):
    domain = cookie["domain"]
    include_subdomain = "TRUE" if domain.startswith(".") else "FALSE"
    path = cookie.get("path", "/")
    secure = "TRUE" if cookie.get("secure", False) else "FALSE"
    expiry = int(cookie.get("expiry", time.time() + 3600))
    name = cookie["name"]
    value = cookie["value"]
    return f"{domain}\t{include_subdomain}\t{path}\t{secure}\t{expiry}\t{name}\t{value}"

def save_netscape_cookies(driver, filename):
    cookies = driver.get_cookies()
    lines = ["# Netscape HTTP Cookie File"]
    for cookie in cookies:
        try:
            lines.append(format_netscape_cookie(cookie))
        except Exception as e:
            print(f"⚠️ Пропущен cookie из-за ошибки: {e}")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    options = uc.ChromeOptions()
    options.add_argument("--user-data-dir=selenium-profile")  # сохраняем сессию
    driver = uc.Chrome(options=options, headless=False)

    driver.get(URL)
    print("➡️ Залогинься вручную, затем нажми Enter здесь...")
    input()

    save_netscape_cookies(driver, COOKIES_TXT)
    print("✅ cookies.txt сохранён!")

    driver.quit()
