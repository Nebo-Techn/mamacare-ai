import asyncio
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class FacebookExtractor:
    """Asynchronous Facebook Post Extractor using Selenium and BeautifulSoup."""

    def __init__(self, email: str, password: str, headless: bool = True):
        self.email = email
        self.password = password

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=chrome_options)

    async def login(self) -> bool:
        """Log into Facebook using Selenium."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.driver.get, "https://www.facebook.com/login")
        await asyncio.sleep(2)

        email_input = await loop.run_in_executor(None, self.driver.find_element, By.ID, "email")
        password_input = await loop.run_in_executor(None, self.driver.find_element, By.ID, "pass")

        await loop.run_in_executor(None, email_input.send_keys, self.email)
        await loop.run_in_executor(None, password_input.send_keys, self.password)

        login_btn = await loop.run_in_executor(None, self.driver.find_element, By.NAME, "login")
        await loop.run_in_executor(None, login_btn.click)

        await asyncio.sleep(3)
        current_url = await loop.run_in_executor(None, lambda: self.driver.current_url)
        return "login" not in current_url

    async def extract_post_text(self, url: str, name: str) -> str:
        """Extract and return the text from a Facebook post."""
        loop = asyncio.get_event_loop()
        print(f"Extracting Facebook post: {name}")

        await loop.run_in_executor(None, self.driver.get, url)
        await asyncio.sleep(4)  # Allow dynamic content to load

        page_source = await loop.run_in_executor(None, lambda: self.driver.page_source)
        soup = BeautifulSoup(page_source, "html.parser")
        posts = soup.find_all("div", {"data-ad-preview": "message"})

        extracted_texts = [p.get_text(" ", strip=True) for p in posts if p.get_text(" ", strip=True)]
        if not extracted_texts:
            print(f"No text found for {name}")
            return ""

        combined = "\n\n".join(extracted_texts)
        print(f"Extracted {len(extracted_texts)} text blocks for {name}")
        return combined

    async def close(self):
        """Gracefully close the Selenium driver."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.driver.quit)


async def extract_facebook_post(url: str, name: str) -> str:
    """Wrapper function for quick use in ingestion pipeline."""
    fb_email = os.getenv("FACEBOOK_EMAIL")
    fb_pass = os.getenv("FACEBOOK_PASSWORD")

    if not fb_email or not fb_pass:
        raise EnvironmentError("Missing FACEBOOK_EMAIL or FACEBOOK_PASSWORD environment variables.")

    scraper = FacebookExtractor(fb_email, fb_pass, headless=True)

    try:
        success = await scraper.login()
        if not success:
            print("Facebook login failed. Check credentials or 2FA.")
            return ""

        content = await scraper.extract_post_text(url, name)
        return content

    finally:
        await scraper.close()
