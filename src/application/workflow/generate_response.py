import uuid
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from typing import Any, AsyncGenerator, Union

from langchain_core.runnables import Runnable
from src.application.workflow.chains import get_chat_title_chain

class Agent:
    def __init__(self, graph: Runnable, llms = []):
        self.llms = llms
        self.graph = graph

    async def get_chat_title(self, messages: list[str] | list[dict[str, any]]):
        count = len(messages)
        should_update = count == 2 or (count > 0 and count % 10 == 0) or count == 1

        print(messages)

        if not should_update:
            return
        
        text_parts = []
        for m in messages:
            # CASO A: Es un objeto de LangChain (HumanMessage, AIMessage)
            if hasattr(m, 'content'):
                text_parts.append(f"{m.type}: {m.content}")
            # CASO B: Es un diccionario simple {'role': '...', 'content': '...'}
            elif isinstance(m, dict):
                text_parts.append(f"{m.get('role')}: {m.get('content')}")
            # CASO C: Es un string suelto
            else:
                text_parts.append(f"user: {str(m)}")

        conversation_text = "\n".join(text_parts)
        llm = self.llms[0]['model']
        chain = get_chat_title_chain(llm=llm)
    
        response = await chain.ainvoke({'conversation': conversation_text})
        return response.content


    async def get_state(self, thread_id: str) -> list:
        config = { 'configurable': { 'thread_id': thread_id } }
        state_snapshot = await self.graph.aget_state(config)

        return state_snapshot

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


      