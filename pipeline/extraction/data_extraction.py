import os
import requests
import time
import whisper

from bs4 import BeautifulSoup
from pathlib import Path
from yt_dlp import YoutubeDL
from urllib.parse import urlparse

import yt_dlp
from pipeline.extraction.db_utils import save_extracted_data
import asyncio

model = whisper.load_model("small")  # or medium/large


# Create a dictionary from your data
data = {
    "Taasisi ya Chakula na Lishe Tanzania": "https://www.tfnc.go.tz/tips/lishe-ya-mama-mjamzito",
    "ada.com website": "https://ada.com/sw/conditions/miscarriage/",
    "open.edu website": "https://www.open.edu/openlearncreate/mod/oucontent/view.php?id=53410&printable=1",
    "Matatizo Madogo ya ujauzito": "https://www.open.edu/openlearncreate/mod/oucontent/view.php?id=53399&printable=1",
    "Kutathmini Mama Mjamzito Kijumla": "https://www.open.edu/openlearncreate/mod/oucontent/view.php?id=53396&printable=1",
    "Mwongozo wa MSD, Toleo la Mtumiaji": "https://www.msdmanuals.com/sw/home/quick-facts-women-s-health-issues/normal-pregnancy/physical-changes-in-the-mother-during-pregnancy",
    "afyamaridhawa.com website": "https://afyamaridhawa.com/zijue-dalili-za-mimba-changa-dalili-12-za-awali/",
    "Idara ya Afya ya Uzazi Mama na Mtoto - Wizara ya Afya": "https://www.instagram.com/afyayamamanamtoto/reel/DDq9OT_tjQB/",
    "Pregnancy Nutrition TZ": "https://www.instagram.com/pregnancy_nutritiontz/",
    "dalili za mimba changa": "https://www.youtube.com/watch?v=zVMo6I5rv2U",
    "ufanye ulta sound ngapi": "https://www.youtube.com/watch?v=gvA7tG0XHlI&pp=0gcJCYUJAYcqIYzv",
    "daili ya mimba wiki 1": "https://www.youtube.com/watch?v=S8ssZBMVtvU",
    "matunda hatari kwa mama mjamzito": "https://www.youtube.com/watch?v=Et89668dNq8",
    "Kwanini mjamzito hukosa hamu ya kula": "https://www.youtube.com/watch?v=5Z_F4oDvmDs&pp=0gcJCYUJAYcqIYzv",
    "je tumbo la mjamzito linaanza kuonekana lini": "https://www.youtube.com/watch?v=XxIKjp8wCAY&pp=0gcJCYUJAYcqIYzv",
    "Tommy's the pregnancy and baby charity": "https://www.tommys.org/pregnancy-information/im-pregnant/pregnancy-calendar/first-trimester-weeks-1-12",
    "Wish Medical": "https://www.wishmedical.com/post/7-questions-to-ask-if-you-re-pregnant",
    "Maisha Huru": "https://www.sw.maishahuru.com/read/dalili-za-mimba-changa-maelezo-na-ufafanuzi-wa-kina-807",
    "Open Learn create": "https://www.open.edu/openlearncreate/mod/oucontent/view.php?id=53395&section=1.4.1",
    "UlyClinic": "https://www.ulyclinic.com/elimu-kwa-mjamzito-magonjwa/wiki-ya-13-ya-ujauzito",
    "BBC1": "https://www.bbc.com/swahili/articles/cj5r6em13ngo",
    "BBC2": "https://www.bbc.com/swahili/articles/c72l2ll026go",
    "BBC3- Jinsi ya kula vizuri wakati wa ujauzito": "https://www.bbc.com/swahili/articles/cn0n097ddk0o",
    "ADA- Utunzaji wa mimba yenye afya": "https://ada.com/sw/editorial/managing-a-healthy-pregnancy/",
    "Apollo Hospitals": "https://www.apollohospitals.com/sw/health-library/bleeding-during-pregnancy",
    "Nini cha kufanya na kuepuka katika trimester ya kwanza ya ujauzito?": "https://continentalhospitals.com/sw/blog/what-to-do-and-avioid-in-the-first-trimester-of-pregnancy/",
    "Maumivu ya Kichwa Wakati wa Ujauzito": "https://afyatrack.com/maumivu-ya-kichwa-wakati-wa-ujauzito/",
    "Tanzmed - Sababu na Dalili za kuharibika mimba sehemu ya 1": "https://tanzmed.co.tz/watoto-uzazi/magonjwa-na-uzazi-wanawake/item/330-kuharibika-kwa-mimba-termination-of-pregnancy-miscarriage-sehemu-ya-kwanza.html",

}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def sanitize_filename(name):
    # Remove invalid characters from filename
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()

def download_audio_from_youtube(url, name, output_dir="./audio"):
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, f"{name}.mp3"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def get_youtube_transcript(url, name):
    """
    Get the transcript of a YouTube video in Swahili. This function uses yt-dlp to download youtube video, and then
    transcript using openai-whisper package.
    Args:
        url (str): The YouTube video URL.
    Returns:
        str: The transcript text in Swahili, or an error message if the transcript cannot be retrieved.
    Raises:
        Exception: If there is an error retrieving the transcript.
    """
    try:
       # download_audio_from_youtube(url, name)
        time.sleep(2)  # Wait for the audio file to be ready
        file = Path("audio") / f"{name}.mp3"
        if not file.exists():
            return f"Error: Audio file {file} not found."
        result = model.transcribe(str(file), language='sw')
        return result['text']
    except Exception as e:
        return f"Error getting YouTube transcript: {str(e)}"

def scrape_website_content(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "aside"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
    except Exception as e:
        return f"Error scraping website: {str(e)}"

def save_content(name, content):
    filename = sanitize_filename(name) + ".txt"
    with open(f"{filename}", 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved content to {filename}")
    # Save to SQLite DB asynchronously
    # Use name, content, and optionally source_url if available
    # If you want to save the source URL, pass it as an argument or fetch from context
    asyncio.run(save_extracted_data("extracted", {"name": name, "content": content}))

def process_links(data):
    for name, url in data.items():
        if not url:
            print(f"Skipping {name} - no URL provided")
            continue

        print(f"Processing {name}...")

        try:
            if 'youtube.com' in url or 'youtu.be' in url:
                content = get_youtube_transcript(url, name)
                save_content(name, content)
                # Also save to DB with source_url
                asyncio.run(save_extracted_data("extracted", {"name": name, "content": content, "source_url": url}))
            # elif 'instagram.com' in url:
            #     content = "Instagram content cannot be scraped directly. Please use Instagram API or manual methods."
            # else:
            #     content = scrape_website_content(url)
            #     save_content(name, content)
            #     asyncio.run(save_extracted_data("extracted", {"name": name, "content": content, "source_url": url}))
        except Exception as e:
            print(f"Error processing {name}: {str(e)}")

if __name__ == "__main__":
    # Create output directory if it doesn't exist
    if not os.path.exists('scraped_content'):
        os.makedirs('scraped_content')
    os.chdir('scraped_content')

    process_links(data)