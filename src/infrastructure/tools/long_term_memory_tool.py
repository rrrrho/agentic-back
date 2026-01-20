from src.application.workflow.long_term_memory_int import LongMemoryToolInterface
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters.base import TextSplitter
from src.config import settings
from bs4 import BeautifulSoup

from playwright.async_api import async_playwright
from langchain_core.documents import Document
from src.config import settings

class LongTermMemoryTool(LongMemoryToolInterface):
    def __init__(self, vector_store: VectorStore, splitter: TextSplitter):
        self.vector_store = vector_store
        self.splitter = splitter

    async def retrieve_context(self, query: str):
        docs = await self.vector_store.asimilarity_search_with_score(query=query, k=3)

        if docs:
            if docs[0][1] < settings.RAG_SCORE_THRESHOLD:
                result = await self.__scrap(query=query)

                docs = self.splitter.create_documents([result['content']], [{ 'source': result['source'] }])

                self.vector_store.add_documents(docs)
        
        return docs
    
    async def __scrap(self, query) -> Document:
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

            text = self.__extract_content(soup)

            await browser.close()

            return { 'content': text, 'source': page.url }
            
    def __extract_content(self, soup: BeautifulSoup):
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
