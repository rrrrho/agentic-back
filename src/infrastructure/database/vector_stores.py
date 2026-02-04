from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain.embeddings import Embeddings
from src.config import settings

def get_mongo_vector_store(embedding: Embeddings) -> MongoDBAtlasVectorSearch:
    return MongoDBAtlasVectorSearch.from_connection_string(
        connection_string=settings.MONGO_URI,
        embedding=embedding,
        namespace=f"{settings.MONGO_DB_NAME}.{settings.MONGO_LONG_TERM_MEMORY_COLLECTION}",
        text_key='chunk',
        embedding_key='embedding',
        relevance_score_fn='dotProduct'
    )
