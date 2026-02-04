from langchain_mongodb.retrievers.hybrid_search import MongoDBAtlasHybridSearchRetriever

def get_mongo_hybrid_search_retriever(vector_store):
    return MongoDBAtlasHybridSearchRetriever(
        vectorstore = vector_store,
        search_index_name = 'hybrid-full-text-search',
        top_k = 1,
        fulltext_penalty = 10,
        vector_penalty = 0
    )
