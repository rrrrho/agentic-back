from abc import ABC, abstractmethod
from langchain_core.tools import tool

class LongMemoryToolInterface(ABC):
    @abstractmethod
    async def search_database(self, query: str):
        pass

    @abstractmethod
    async def web_search(self, query: str):
        pass

def create_search_database_tool(retriever: LongMemoryToolInterface):

    @tool
    async def search_database(query: str):
        '''
        Use this tool to perform a search in the vector database based on the provided query.
        '''
        docs = await retriever.search_database(query=query)

        if isinstance(docs, list):
            return "\n\n".join([doc.page_content for doc in docs])
        return str(docs)
    
    return search_database

def create_web_search_tool(retriever: LongMemoryToolInterface):

    @tool
    async def web_search(query: str):
        '''
        Use this tool to perform a web search based on the provided query.
        '''
        docs = await retriever.web_search(query=query)

        if isinstance(docs, list):
            return "\n\n".join([doc.page_content for doc in docs])
        return str(docs)
    
    return web_search