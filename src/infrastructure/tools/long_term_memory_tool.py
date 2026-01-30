from src.application.memory.long_term_memory_int import LongMemoryToolInterface
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters.base import TextSplitter
from src.application.memory.scraper import ScraperInterface
from src.config import settings

class LongTermMemoryTool(LongMemoryToolInterface):
    def __init__(self, vector_store: VectorStore, retriever, splitter: TextSplitter, web_search_engine):
        self.vector_store = vector_store
        self.splitter = splitter
        self.retriever = retriever
        self.web_search_engine = web_search_engine

    async def search_database(self, query: str):
        docs = self.retriever.invoke(input=query)

        print('\nDOCS: ', docs, '\n')

        return docs
    
    async def web_search(self, query: str):
        print('\QUERY: ', query, '\n')
        results = self.web_search_engine.web_search(query=query)

        print('\nWEB: ', results, '\n')

        context = []
        for result in results:

            docs = self.splitter.create_documents([result.text], [result.metadata])
            context.extend(docs)

        await self.vector_store.aadd_documents(context)

        return context
