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
        Busca noticias de último minuto, eventos actuales y datos en tiempo real.
        Úsala OBLIGATORIAMENTE cuando el usuario pregunte sobre hechos ocurridos recientemente,
        situaciones políticas actuales, resultados deportivos, clima, o cualquier dato que 
        requiera precisión cronológica del año 2024 en adelante.
        No confíes en tu conocimiento interno para temas de actualidad; utiliza siempre esta herramienta.
        '''
        return await retriever.retrieve_context(query=query)
    
    return retrieve_context