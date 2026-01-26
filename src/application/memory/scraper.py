from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ScrapText:
    text: str
    metadata: dict

class ScraperInterface(ABC):

    @abstractmethod
    def scrap(self, query: str) -> list[ScrapText]:
        pass