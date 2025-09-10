import fitz  # PyMuPDF
import asyncio
from typing import List

async def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text.append(page.get_text())
    doc.close()
    return "\n".join(text)

async def extract_texts_from_pdfs(pdf_paths: List[str]) -> List[str]:
    tasks = [extract_text_from_pdf(path) for path in pdf_paths]
    return await asyncio.gather(*tasks)
