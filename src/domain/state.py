from langgraph.graph import MessagesState

class CustomState(MessagesState):
    summary: str
    context: str