from abc import ABC, abstractmethod

class Metasearch(ABC):
    @abstractmethod
    def web_search(self, query: str): pass