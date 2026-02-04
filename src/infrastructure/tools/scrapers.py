from src.application.memory.scraper import ScrapText, ScraperInterface
from bs4 import BeautifulSoup

from playwright.async_api import async_playwright
from langchain_core.documents import Document

class CNNScraper(ScraperInterface):
    url = 'https://edition.cnn.com/'

    async def scrap(self, query: str) -> list[ScrapText]:

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1500)
            page = await browser.new_page()

            await page.goto(url=self.url)

            cookies_button = page.locator('button[id=onetrust-accept-btn-handler]')
            await cookies_button.click()

            search_button = page.locator('button[id=headerSearchIcon]')
            await search_button.click()

            search_bar = page.locator('.search-bar__input').first
            await search_bar.fill(query)
            await search_bar.press('Enter')

            stories_button = page.locator('.facet__item').nth(1)
            await stories_button.click()

            data = []
            for i in range(2):
                article = page.locator('.container__headline-text').nth(i)
                await article.click()

                html_content = await page.content()
                soup: BeautifulSoup = BeautifulSoup(html_content, "html.parser")

                text = self.__extract_content(soup)
                metadata = { 'source': page.url }
                data.append(ScrapText(text=text, metadata=metadata))

                await page.go_back()

            await browser.close()

            return data
    
    def __extract_content(self, soup: BeautifulSoup):
        excluded_sections = [
            'image_large__container',
            'image__container',
            'layout-article-elevate__top layout__top',
            'layout-article-elevate__breadcrumb',
            'layout-article-elevate__lede',
            'layout-article-elevate__info',
            'layout__left layout-article-elevate__left tabcontent active',
            'Embed',
            'image__metadata-wrapper',
            'layout-article-elevate__bottom',
            'onetrust-consent-sdk'
        ]

        for section_name in excluded_sections:
            for section in soup.find_all(class_=section_name):
                section.decompose()

            for section in soup.find_all(['button', 'em', 'footer', 'header', 'aside', 'iframe', 'img']):
                section.decompose()

            for section in soup.find_all('em'):
                section.decompose()
            
            for section in soup.find_all(id=section_name):
                section.decompose()

            for section in soup.find_all(lambda tag: tag.has_attr("id") and section_name in tag["id"].lower()):
                section.decompose()

            for section in soup.find_all(lambda tag: tag.has_attr("class") and any(section_name in cls.lower() for cls in tag["class"])):
                section.decompose()

        content = []
        for element in soup.find_all(["p", "h1", "h2", "h3"]):
            content.append(element.get_text())

        return "\n".join(content)


class LaNacionScraper(ScraperInterface):
    url = 'https://www.lanacion.com.ar/'

    async def scrap(self, query) -> Document:

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, slow_mo=1000)
            page = await browser.new_page()

            await page.goto(url=self.url)

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

