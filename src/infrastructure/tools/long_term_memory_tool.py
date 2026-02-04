from src.application.memory.long_term_memory_int import LongMemoryToolInterface
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters.base import TextSplitter
from src.application.memory.metasearch_engine_int import Metasearch

class LongTermMemoryTool(LongMemoryToolInterface):
    def __init__(self, vector_store: VectorStore, retriever, splitter: TextSplitter, web_search_engine: Metasearch):
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

            docs = self.splitter.create_documents([result['text']], [result['metadata']])
            context.extend(docs)

        await self.vector_store.aadd_documents(context)

        fragments = await self.search_database(query=query)

        return fragments
