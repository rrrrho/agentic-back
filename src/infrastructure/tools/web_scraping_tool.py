import asyncio
from bs4 import BeautifulSoup
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from playwright.async_api import async_playwright
from langchain_core.documents import Document
from pymongo import AsyncMongoClient

from src.infrastructure.database.splitters import get_splitter
from src.config import settings

client = AsyncMongoClient(settings.MONGO_URI, appname='agentic-back')
collection = client[settings.MONGO_DB_NAME][settings.MONGO_LONG_TERM_MEMORY_COLLECTION]

embedding = HuggingFaceEmbeddings(
    model_name=settings.RAG_TEXT_EMBEDDING_MODEL_ID,
    model_kwargs={"device": settings.RAG_DEVICE, "trust_remote_code": True},
    encode_kwargs={"normalize_embeddings": False}
)

vector_store = MongoDBAtlasVectorSearch.from_connection_string(
    connection_string=settings.MONGO_URI,
    embedding=embedding,
    namespace=f"{settings.MONGO_DB_NAME}.{settings.MONGO_LONG_TERM_MEMORY_COLLECTION}",
    text_key="chunk",
    embedding_key="embedding",
    relevance_score_fn="dotProduct"
)


async def save_context(query: str):
    doc = await scrap(query)

    splitter = get_splitter(chunk_size=settings.RAG_CHUNK_SIZE)
    chunked_docs = splitter.split_documents([doc])

    print(chunked_docs)
    vector_store.add_documents([doc])

    

async def scrap(query) -> Document:
    URL = 'https://www.lanacion.com.ar/'

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=1000)
        page = await browser.new_page()

        await page.goto(url=URL)

        search_button = page.locator('label[title="Ir al buscador"]')
        await search_button.click()

        search_bar = page.locator('input[id=queryly_query]')
        await search_bar.fill(query)
        await search_bar.press('Enter')

        result_item = page.locator('.resultlink.double-teaser__title').first
        await result_item.click()

        html_content = await page.content()
        soup: BeautifulSoup = BeautifulSoup(html_content, "html.parser")

        text = extract_content(soup)
        metadata = {
            'source': page.url
        }

        if h1 := soup.find('h1'):
            metadata['title'] = h1.get_text().strip(" \n")

        await browser.close()

        return text
        
def extract_content(soup: BeautifulSoup):
    excluded_sections = [
        'ln-banner-container',
        'lay --apertura',
        'sidebar__aside hlp-tabletlm-none',
        'v-share',
        'button-play',
        'image',
        'ln-text',
        'box-articles',
        'newsletterbox',
        'message',
        'comments-viafoura',
        'footer-container',
        'header-container',
        'com-breadcrumb',
        'mod-opening',
        'mod-date-container',
        'button'
    ]

    for section_name in excluded_sections:
        for section in soup.find_all(class_=section_name):
            section.decompose()
        
        for section in soup.find_all(id=section_name):
            section.decompose()

        for section in soup.find_all(lambda tag: tag.has_attr("id") and section_name in tag["id"].lower()):
            section.decompose()

        for section in soup.find_all(lambda tag: tag.has_attr("class") and any(section_name in cls.lower() for cls in tag["class"])):
            section.decompose()

    content = []
    for element in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"]):
        content.append(element.get_text())

    return "\n\n".join(content)



#res = vector_store.similarity_search(query='cuando viene bts a argentina')
if __name__ == "__main__":
    # Opción A: Ejecutar solo el scrap e imprimir
    res = asyncio.run(scrap('cuando viene bts a argentina'))
    docs = get_splitter(chunk_size=256).create_documents([res])
    print(docs)

