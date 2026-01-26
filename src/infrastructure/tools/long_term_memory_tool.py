from src.application.memory.long_term_memory_int import LongMemoryToolInterface
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters.base import TextSplitter
from src.application.memory.scraper import ScraperInterface
from src.config import settings

class LongTermMemoryTool(LongMemoryToolInterface):
    def __init__(self, vector_store: VectorStore, retriever, splitter: TextSplitter, scraper: ScraperInterface):
        self.vector_store = vector_store
        self.splitter = splitter
        self.retriever = retriever
        self.scraper = scraper

    async def retrieve_context(self, query: str):
        docs = self.retriever.invoke(input=query)

        score = 0
        if docs:
            score = docs[0].metadata['score']

        print('\n\nSCORE: ', score, '\n\n')
        if not docs or score < settings.RAG_SCORE_THRESHOLD:

            results = self.scraper.scrap(query=query)

            context = []
            for result in results:

                docs = self.splitter.create_documents([result.text], [result.metadata])
                context.extend(docs)

            await self.vector_store.aadd_documents(context)

            return context

        return docs
