from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from langchain_core.documents import Document
from langchain_core.tools import tool

@tool('web_search')
async def search(self, query) -> Document:
    url = 'https://www.lanacion.com.ar/'

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()

        await page.goto(url=url)

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

        return Document(page_content=text, metadata=metadata)
        
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


