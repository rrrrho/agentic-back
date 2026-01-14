from typing import Generic, Type, TypeVar
from bson import ObjectId
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from src import settings

T = TypeVar("T", bound=BaseModel)

class MongoClientWrapper(Generic[T]):

    def __init__(
            self, 
            model: Type[T],
            collection_name: str, 
            database_name: str = settings.MONGO_DB_NAME, 
            mongodb_uri: str = settings.MONGO_URI
        ) -> None:
        
        self.model = model
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.collection_name = collection_name

        try:
            self.client = MongoClient(mongodb_uri, appname='agentic-back')
            self.client.admin.command('ping')
        except Exception as err:
            raise err
        
        self.database = self.client[database_name]
        self.collection = self.database[collection_name]

    # context manager
    def __enter__(self) -> 'MongoClientWrapper':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """close the MongoDB connection.

        this method should be called when the service is no longer needed
        to properly release resources, unless using the context manager.
        """

        self.client.close()
        
    # mongo api
    def insert_documents(self, documents: list[T]) -> None:
        try:
            if not documents or not all(isinstance(doc, BaseModel) for doc in documents):
                raise ValueError('documents must be a list of Pydantic models')
            
            dict_documents = [doc.model_dump() for doc in documents]

            # remove id fields to avoid duplicate key errors
            for doc in dict_documents:
                doc.pop('_id', None)

            self.collection.insert_many(dict_documents)

        except Exception as err:
            raise

    def fetch_documents(self, limit: int, query: dict) -> list[T]:
        try:
            documents = list(self.collection.find(query).limit(limit))
            return self.__parse_documents(documents)
        except Exception as err:
            raise

    # utilities   
    def __parse_documents(self, documents: list[dict]) -> list[T]:
        parsed_documents = []
        for doc in documents:
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    doc[key] = str(value)

            _id = doc.pop('_id', None)
            doc['id'] = _id

            parsed_doc = self.model.model_validate(doc)
            parsed_documents.append(parsed_doc)

        return parsed_documents


        
