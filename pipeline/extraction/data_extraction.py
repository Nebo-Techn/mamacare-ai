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
    "dalili-kuu-za-mwanzo-za-mimba-changa-kwaanzia-siku-za-mwanzo":"https://bongoclass.com/dalili-kuu-za-mwanzo-za-mimba-changa-kuanzia-siku-ya-kwanza",
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
    "Kudhibiti Kichefuchefu Wakati wa Ujauzito":"https://www.medicoverhospitals.in/sw/articles/tips-to-deal-with-vomiting-during-pregnancy",
    "jinsi-ya-kupunguza-kichefuchefu-na-kutapika-wakati-wa-ujauzito":"https://medikea.co.tz/blog/jinsi-ya-kupunguza-kichefuchefu-na-kutapika-wakati-wa-ujauzito",
     "dalili-za-mimba-wiki-ya-kwanza":"https://medikea.co.tz/blog/dalili-za-mimba-wiki-ya-kwanza",
     "je-ni-sawa-kuendelea-kunyonyesha-mtoto-wakati-una-mimba-nyingine":"https://medikea.co.tz/blog/je-ni-sawa-kuendelea-kunyonyesha-mtoto-wakati-una-mimba-nyingine",
     "kwa-nini-mama-mjamzito-hapaswi-kulala-chali":"https://medikea.co.tz/blog/kwa-nini-mama-mjamzito-hapaswi-kulala-chali",
     "Dalili na Sababu za Ugonjwa wa Asubuhi":"https://www.medicoverhospitals.in/sw/diseases/morning-sickness/",
     "kwanini-kutapika-nyongo-kwa-mama-mjamzito":"https://www.ulyclinic.com/foramu/majadiliano-na-wataalamu/kwanini-kutapika-nyongo-kwa-mama-mjamzito",
     "siri-nzito-kichefuchefu-kutapika-wakati-wa-ujauzito":"https://www.mwananchi.co.tz/mw/habari/makala/afya/siri-nzito-kichefuchefu-kutapika-wakati-wa-ujauzito-2763260",
     "sababu-mazoezi-kuwa-muhimu-kwa-mjamzito":"https://www.mwananchi.co.tz/mw/habari/makala/afya/sababu-mazoezi-kuwa-muhimu-kwa-mjamzito-4916626",
     "Mazoezi Salama kwa Akina Mama Wanaotarajia":"https://www.medicoverhospitals.in/sw/articles/pregnancy-fitness-guide-safe-exercises",
     "Kurudi Katika Umbo Baada ya Lishe ya Kuzaa na Mazoezi Kwa Mama Wapya":"https://www.medicoverhospitals.in/sw/articles/getting-back-in-shape-after-childbirth",
     "umuhimu-wa-mazoezi-kabla-na-baada-ya-kujifungua":"https://afyatrack.com/umuhimu-wa-mazoezi-kabla-na-baada-ya-kujifungua/",
     "Fanya Mazoezi Wakati Wa Ujauzito":"https://www.edhacare.com/sw/blogs/exercise-during-pregnancy/",
     "nitarajie-nini-mwili-wangu-unapopona-baada-ya-kujifungua":"https://www.msdmanuals.com/sw/home/quick-facts-women-s-health-issues/postpartum-care/overview-of-postpartum-care#Je,-nitarajie-nini-mwili-wangu-unapopona-baada-ya-kujifungua?_v39461885_sw",
     "huu-ndio-utaratibu-wa-kufanya-mazoezi-baada-ya-kujifungua-kwa-upasuaji":"https://medikea.co.tz/blog/huu-ndio-utaratibu-wa-kufanya-mazoezi-baada-ya-kujifungua-kwa-upasuaji",
     "Wanawake wanafaa kutembea wakati wa ujauzito":"https://www.bbc.com/swahili/articles/cjq7jnvkd8do",
     "Dalili za Maumivu ya Kinyonga":"https://www.medicoverhospitals.in/sw/symptoms/hip-pain",
     "Ulifanya kazi siku nzima":"https://www.apollohospitals.com/sw/diseases-and-conditions/hip-arthritis-hip-surgical-and-non-surgical-treatment",
     "Dalili za Maumivu ya Pelvic":"https://www.medicoverhospitals.in/sw/symptoms/pelvic-pain",
     "maumivu ya sehemu ya chini ya mgongo":"https://www.msdmanuals.com/sw/home/multimedia/video/what-causes-low-back-pain",
     "mama-mjamzito-wa-miezi-sita-anaweza-kusafiri-umbali-mrefu":"https://www.ulyclinic.com/majibu-ya-maswali/je%2C-mama-mjamzito-wa-miezi-sita-anaweza-kusafiri-umbali-mrefu%3F",
     "Kujitunza Wakati wa Ujauzito":"https://www.msdmanuals.com/sw/home/quick-facts-women-s-health-issues/normal-pregnancy/taking-care-of-yourself-during-pregnancy",
     "Zijue Tahadhari Wakati Wa Ujauzito":"https://www.medicoverhospitals.in/sw/articles/precautions-during-pregnancy",
     "kusafiri-wakati-wa-ujauzito":"https://ciconea.com/sw/kusafiri-wakati-wa-ujauzito/",
     "asidi-ya-folic-wakati-wa-ujauzito-a":"https://ciconea.com/sw/asidi-ya-folic-wakati-wa-ujauzito-a/",
     "watoto-wachanga-wanahitaji-vitamini":"https://ciconea.com/sw/kwa-nini-watoto-wachanga-wanahitaji-vitamini-D/",
     "ugonjwa-wa-kisukari-wa-ujauzito-kula":"https://ciconea.com/sw/ugonjwa-wa-kisukari-wa-ujauzito-kula/",
     "harufu-kali-ya-mwili-wakati-wa-ujauzito":"https://www.ulyclinic.com/post/harufu-kali-ya-mwili-wakati-wa-ujauzito",
     "husababisha harufu mbaya ya kinywa na inaweza kutibiwa":"https://www.bbc.com/swahili/articles/c9dgvxy98d9o",
     "Dalili za Harufu mbaya":"https://www.medicoverhospitals.in/sw/symptoms/bad-breath"

     }
facebooks_links = {
    "mama-mjamzito-mazoezi-rahisi-kwa-ajili-ya-kunyoosha-viungo-kila-asubuhi-ni-muhim": "https://www.facebook.com/MamaKitTanzania/posts/mama-mjamzito-mazoezi-rahisi-kwa-ajili-ya-kunyoosha-viungo-kila-asubuhi-ni-muhim/112850947453265/",
    "hapa-kuna-mpangilio-mzuri-unaovutia-na-rahisi-kusomamaumivu-ya-nyonga-sababu":"https://www.facebook.com/100063619116074/posts/hapa-kuna-mpangilio-mzuri-unaovutia-na-rahisi-kusomamaumivu-ya-nyonga-sababu-na-/1216951190435507/",
    "sababu-10-za-maumivu-ya-kiuno-nyonga-chini-ya-kitovu-kwa-wanawakehaya-ni-maumivu":"https://www.facebook.com/100063615877937/posts/sababu-10-za-maumivu-ya-kiuno-nyonga-chini-ya-kitovu-kwa-wanawakehaya-ni-maumivu/970594813457215/",
    "kuhusu-watoto-wachanga-kupanda-ndege-na-uraia-wa-kuzaliwa-angani-ingawa-watoto":"https://www.facebook.com/aviationmediatz/posts/kuhusu-watoto-wachanga-kupanda-ndege-na-uraia-wa-kuzaliwa-angani-ingawa-watoto-w/893541048094339/",
    "mama-mjamzito-ni-vema-kuweza-kusafiri-kuanzia-mimba-yenye-umri-wa-wiki-14-hadi":"https://www.facebook.com/JapideAfya/posts/mama-mjamzito-ni-vema-kuweza-kusafiri-kuanzia-mimba-yenye-umri-wa-wiki-14-hadi-w/381720856572656/",
    "kutokwa-na-harufu-mbaya-mdomoni-halitosis-tatizo-hili-la-kutokwa-na-harufu-mbaya":"https://www.facebook.com/100063921285190/posts/kutokwa-na-harufu-mbaya-mdomoni-halitosis-tatizo-hili-la-kutokwa-na-harufu-mbaya/1187082312111069/"
}

instagram_links = {
    "Mazoezi yana faida kubwa kwa wanawake":"https://www.instagram.com/p/DA44pwmoRlR/?hl=en",

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
        download_audio_from_youtube(url, name)
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

def save_content(name, content, source_url):
    filename = sanitize_filename(name) + ".txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved content to {filename}")
    # Save to SQLite DB asynchronously
    # Use name, content, and optionally source_url if available
    # If you want to save the source URL, pass it as an argument or fetch from context
    asyncio.run(save_extracted_data("extracted", {"name": name, "content": content, "source_url": source_url}))

def process_links(data):
    for name, url in data.items():
        if not url:
            print(f"Skipping {name} - no URL provided")
            continue

        print(f"Processing {name}...")

        try:
            if 'youtube.com' in url or 'youtu.be' in url:
                content = get_youtube_transcript(url, name)
            else:
                content = scrape_website_content(url)
            save_content(name, content, url)
        except Exception as e:
            print(f"Error processing {name}: {str(e)}")

if __name__ == "__main__":
    # Create output directory if it doesn't exist
    if not os.path.exists('scraped_content'):
        os.makedirs('scraped_content')
    os.chdir('scraped_content')

    process_links(data)