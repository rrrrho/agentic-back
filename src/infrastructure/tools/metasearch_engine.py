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

        try:
            response = requests.post(url, data=payload, timeout=5).json()
        except requests.exceptions.RequestException as e:
            print(f"error connecting to SearXNG: {e}")
            return []

        urls = self.get_urls(data=response, quantity=urls_to_scrap)

        data = []
        for url in urls:
            try: 
                html = requests.get(url, timeout=10)

                html.raise_for_status()

                content = BeautifulSoup(html.content, 'html.parser')
                cleaned_content = self.clean_html(html=content)

                metadata = { 'source': url }
                data.append({'text': cleaned_content, 'metadata': metadata})

            except requests.RequestException as err:
                print(f"URL {url} timeout: {err}")
                continue

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


