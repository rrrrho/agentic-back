from abc import ABC, abstractmethod
from langchain_core.tools import tool

class LongMemoryToolInterface(ABC):
    @abstractmethod
    async def retrieve_context(self, query: str):
        pass

def create_retrieve_context_tool(retriever: LongMemoryToolInterface):

    @tool
    async def retrieve_context(query: str):
        '''
        ALWAYS use this tool whenever the user asks about news, current events, 
        sports results, or facts that occurred after your training cutoff date and you do not 
        have the information to answer. 
        DO NOT try to guess current information. 
        '''
        docs = await retriever.retrieve_context(query=query)

        if isinstance(docs, list):
            return "\n\n".join([doc.page_content for doc in docs])
        return str(docs)
    
    return retrieve_context