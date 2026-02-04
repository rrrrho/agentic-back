from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from typing import Any, AsyncGenerator, Union

from langchain_core.runnables import Runnable

class Agent:
    def __init__(self, graph: Runnable):
        self.graph = graph

    async def get_response(self, messages: str | list[str] | list[dict[str, any]], thread_id: str) -> AsyncGenerator[str, None]:
                
        config = { "configurable": { "thread_id": thread_id } }

        # asStream emits events for every action the agent performs. doesn't wait for end result.
        async for chunk in self.graph.astream(
            input = { 'messages': self.__format_messages(messages=messages) },
            config = config,
            stream_mode = 'messages'):
                
                # filters non content (it emits technical events)
                if chunk[1]['langgraph_node'] == 'conversation_node' and isinstance(chunk[0], AIMessageChunk) and chunk[0].content != '':
                    # sends text fragments until response is fully completed
                    yield chunk[0].content

    def __format_messages(self, messages: Union[str, list[dict[str, Any]]]) -> list[Union[HumanMessage, AIMessage]]:
        """convert various message formats to a list of LangChain message objects.

        args:
            messages: can be one of:
                - a single string message.
                - a list of string messages.
                - a list of dictionaries with 'role' and 'content' keys.

        returns:
            List[Union[HumanMessage, AIMessage]]: a list of LangChain message objects.
        """

        if isinstance(messages, str):
            return [HumanMessage(content=messages)]

        if isinstance(messages, list):
            if not messages:
                return []

            if (
                isinstance(messages[0], dict)
                and "role" in messages[0]
                and "content" in messages[0]
            ):
                result = []
                for msg in messages:
                    if msg["role"] == "user":
                        result.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        result.append(AIMessage(content=msg["content"]))
                return result

            return [HumanMessage(content=message) for message in messages]

        return []


      