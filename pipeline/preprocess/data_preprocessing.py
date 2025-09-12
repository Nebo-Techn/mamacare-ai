import os
from pathlib import Path
import textwrap
import pickle

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

chunks = []

# Load web content
for file in Path("scraped_content").glob("*.txt"):
    url = data.get(file.stem, "") 
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

    for chunk in textwrap.wrap(text, width=500):
        if len(chunk.strip()) > 100:
            chunks.append({
                "text": chunk.strip(),
                "source": url
            })

print(f"Total chunks created: {len(chunks)}")   
print(f"Example chunk: {chunks[-5:]}")
# Save as pickle
with open("trimester1_chunks.pkl", "wb") as f:
    pickle.dump(chunks, f)
