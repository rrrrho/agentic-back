from typing_extensions import Literal
from src.domain.state import CustomState
from src.config import settings
from langgraph.graph import END

def should_summarize_conversation(state: CustomState) -> Literal['summarize_conversation_node', '__end__']:
    messages = state['messages']

    if len(messages) > settings.TOTAL_MESSAGES_SUMMARY_TRIGGER:
        return 'summarize_conversation_node'
    
    return END