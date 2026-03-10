from langgraph.graph import MessagesState

class ImageState(MessagesState):
    prompt: str
    request: str
    image_url: str