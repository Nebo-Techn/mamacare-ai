from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import asyncio
import time
import os
from bs4 import BeautifulSoup

class FacebookScraper:
    async def close(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.driver.quit)
    def __init__(self, email: str, password: str, headless: bool = True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.email = email
        self.password = password

    async def login(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.driver.get, 'https://www.facebook.com/login')
        await asyncio.sleep(2)
        email_input = await loop.run_in_executor(None, self.driver.find_element, By.ID, 'email')
        password_input = await loop.run_in_executor(None, self.driver.find_element, By.ID, 'pass')
        await loop.run_in_executor(None, email_input.send_keys, self.email)
        await loop.run_in_executor(None, password_input.send_keys, self.password)
        login_btn = await loop.run_in_executor(None, self.driver.find_element, By.NAME, 'login')
        await loop.run_in_executor(None, login_btn.click)
        await asyncio.sleep(3)
        current_url = await loop.run_in_executor(None, lambda: self.driver.current_url)
        if "login" not in current_url:
            print("Login successful!")
            return True
        else:
            print("Login failed!")
            return False

    async def navigate_to_group(self, group_url: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.driver.get, group_url)
        await asyncio.sleep(3)
        print(f"Navigated to {group_url}")

    async def infinite_scroll(self, scroll_count: int = 10, pause: float = 2.0):
        loop = asyncio.get_event_loop()
        for i in range(scroll_count):
            await loop.run_in_executor(None, self.driver.execute_script, "window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(pause)
            print(f"Scrolled {i+1}/{scroll_count}")

    async def extract_posts(self):
        loop = asyncio.get_event_loop()
        page_source = await loop.run_in_executor(None, lambda: self.driver.page_source)
        soup = BeautifulSoup(page_source, 'html.parser')
        # Example: Find post containers (update selector as needed)
        posts = soup.find_all('div', {'data-ad-preview': 'message'})
        extracted = []
        for post in posts:
            text = post.get_text(separator=' ', strip=True)
            extracted.append(text)
        print(f"Extracted {len(extracted)} posts.")
        return extracted

# Usage example:
async def main():
    scraper = FacebookScraper('abdillahissa866@gmail.com', 'Password@#21')
    await scraper.login()
    group_url = 'https://www.facebook.com/afyayauzazinamtoto.co/posts/chakula-cha-mama-mjamzitokwa-ajili-afya-ya-mama-na-mtoto-ni-muhimu-sana-mwanamke/963725485742086/'  # Replace with actual group/channel URL
    await scraper.navigate_to_group(group_url)
    await scraper.infinite_scroll(scroll_count=10, pause=2.0)
    posts = await scraper.extract_posts()
    for i, post in enumerate(posts, 1):
        print(f"Post {i}: {post}\n")
        filename = f"post_{i}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(post)
        print(f"Saved post {i} to {filename}")
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
