from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import asyncio
import time
import os
from bs4 import BeautifulSoup

facebook_links = {
    "mama-mjamzito-mazoezi-rahisi-kwa-ajili-ya-kunyoosha-viungo-kila-asubuhi-ni-muhim": "https://www.facebook.com/MamaKitTanzania/posts/mama-mjamzito-mazoezi-rahisi-kwa-ajili-ya-kunyoosha-viungo-kila-asubuhi-ni-muhim/112850947453265/",
    "hapa-kuna-mpangilio-mzuri-unaovutia-na-rahisi-kusomamaumivu-ya-nyonga-sababu":"https://www.facebook.com/100063619116074/posts/hapa-kuna-mpangilio-mzuri-unaovutia-na-rahisi-kusomamaumivu-ya-nyonga-sababu-na-/1216951190435507/",
    "sababu-10-za-maumivu-ya-kiuno-nyonga-chini-ya-kitovu-kwa-wanawakehaya-ni-maumivu":"https://www.facebook.com/100063615877937/posts/sababu-10-za-maumivu-ya-kiuno-nyonga-chini-ya-kitovu-kwa-wanawakehaya-ni-maumivu/970594813457215/",
    "kuhusu-watoto-wachanga-kupanda-ndege-na-uraia-wa-kuzaliwa-angani-ingawa-watoto":"https://www.facebook.com/aviationmediatz/posts/kuhusu-watoto-wachanga-kupanda-ndege-na-uraia-wa-kuzaliwa-angani-ingawa-watoto-w/893541048094339/",
    "mama-mjamzito-ni-vema-kuweza-kusafiri-kuanzia-mimba-yenye-umri-wa-wiki-14-hadi":"https://www.facebook.com/JapideAfya/posts/mama-mjamzito-ni-vema-kuweza-kusafiri-kuanzia-mimba-yenye-umri-wa-wiki-14-hadi-w/381720856572656/",
    "kutokwa-na-harufu-mbaya-mdomoni-halitosis-tatizo-hili-la-kutokwa-na-harufu-mbaya":"https://www.facebook.com/100063921285190/posts/kutokwa-na-harufu-mbaya-mdomoni-halitosis-tatizo-hili-la-kutokwa-na-harufu-mbaya/1187082312111069/"
}

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

    async def extract_and_save_posts(self, links_dict):
        loop = asyncio.get_event_loop()
        os.makedirs("facebook_posts", exist_ok=True)
        for name, url in links_dict.items():
            print(f"Processing: {name}")
            await loop.run_in_executor(None, self.driver.get, url)
            await asyncio.sleep(3)
            page_source = await loop.run_in_executor(None, lambda: self.driver.page_source)
            soup = BeautifulSoup(page_source, 'html.parser')
            posts = soup.find_all('div', {'data-ad-preview': 'message'})
            extracted = []
            for post in posts:
                text = post.get_text(separator=' ', strip=True)
                if text:
                    extracted.append(text)
            print(f"Extracted {len(extracted)} posts for {name}.")
            for i, post in enumerate(extracted, 1):
                filename = f"facebook_posts/{name}_post_{i}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(post)
                print(f"Saved post {i} for {name} to {filename}")

# Usage example:
async def main():
    scraper = FacebookScraper('abdillahissa866@gmail.com', 'Password@#21')
    await scraper.login()
    await scraper.extract_and_save_posts(facebook_links)
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
