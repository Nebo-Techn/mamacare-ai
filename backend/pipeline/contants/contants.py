from pathlib import Path

# Base directory for storing scraped or processed content
BASE_DIR = Path(__file__).resolve().parent

# Directory for audio downloads or transcriptions
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

# Directory for text scraped content
SCRAPED_DIR = BASE_DIR / "scraped_content"
SCRAPED_DIR.mkdir(exist_ok=True)

TEXT_DIR = Path("data/texts")
TEXT_DIR.mkdir(parents=True, exist_ok=True)