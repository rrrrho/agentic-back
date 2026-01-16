from abc import ABC, abstractmethod

class SearchToolInterface(ABC):
    @abstractmethod
    async def search(self, query: str) -> str:
        pass