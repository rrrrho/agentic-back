from pydantic import BaseModel

class User(BaseModel):
    _id: str
    name: str
    email: str
    password: str
