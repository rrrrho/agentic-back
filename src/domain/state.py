from langgraph.graph import MessagesState

class CustomState(MessagesState):
    user_query: str
    summary: str
    context: str
    retry_count: int = 0
    validation_status: str