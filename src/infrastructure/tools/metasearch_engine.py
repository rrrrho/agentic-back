import requests

from bs4 import BeautifulSoup
from src.application.memory.metasearch_engine_int import Metasearch
from src.config import settings

class SearXNGWebSearchEngine(Metasearch):
    def web_search(self, query: str) -> str:
        url = settings.METASEARCH_URL
        payload = {
            "q": query,
            "format": "json"
        }
        urls_to_scrap = settings.URL_SCRAP_QUANTITY

        response = requests.post(url, data=payload).json()
        urls = self.get_urls(data=response, quantity=urls_to_scrap)

        data = []
        for url in urls:
            html = requests.get(url)
            content = BeautifulSoup(html.content, 'html.parser')
            cleaned_content = self.clean_html(html=content)

            metadata = { 'source': url }
            data.append({'text': cleaned_content, 'metadata': metadata})

        return data
        
    def clean_html(self, html: BeautifulSoup):
        content = ''
        for element in html.find_all(['p', 'h1', 'h2', 'h3', 'h4']):
            content += element.get_text()

            if element.name in ['h1', 'h2', 'h3', 'h4']:
                content += '.'

            content += ' '

        return content.replace('\n', '').strip()

    def get_urls(self, data, quantity: int = 3):
        return [data['results'][i]['url'] for i in range(quantity)]


