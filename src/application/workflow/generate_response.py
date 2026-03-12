import uuid
from bson import ObjectId
from langchain.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, RemoveMessage
from typing import Any, AsyncGenerator, Union

from langchain_core.runnables import Runnable
from pydantic import BaseModel
from src.application.workflow.chains import get_chat_title_chain

class LanguageModels(BaseModel):
    chat_model: BaseChatModel
    summary_model: BaseChatModel
    image_model: BaseChatModel

class Agent:
    def __init__(self, graph: Runnable, image_graph: Runnable, llms = LanguageModels):
        self.llms = llms
        self.graph = graph
        self.image_graph = image_graph

    async def generate_image(self, message: str, thread_id: str):
        config = { 'configurable': { 'thread_id': ObjectId(thread_id) } }

        response = await self.image_graph.ainvoke(
            {
                'request': message,
            },
            config= config
        )

        return response.get('image_url', '')

    async def get_chat_title(self, messages: list[str] | list[dict[str, any]]):
        count = len(messages)
        should_update = count == 2 or (count > 0 and count % 10 == 0) or count == 1

        if not should_update:
            return
        
        text_parts = []
        for m in messages:
            # LangChain object (HumanMessage, AIMessage)
            if hasattr(m, 'content'):
                text_parts.append(f"{m.type}: {m.content}")
            # simple dic {'role': '...', 'content': '...'}
            elif isinstance(m, dict):
                text_parts.append(f"{m.get('role')}: {m.get('content')}")
            # string
            else:
                text_parts.append(f"user: {str(m)}")

        conversation_text = "\n".join(text_parts)
        llm = self.llms.summary_model
        chain = get_chat_title_chain(llm=llm)
    
        response = await chain.ainvoke({'conversation': conversation_text})
        return response.content


    async def get_state(self, thread_id: str) -> list:
        config = { 'configurable': { 'thread_id': ObjectId(thread_id) } }
        state_snapshot = await self.graph.aget_state(config)

        return state_snapshot

    async def get_response(self, messages: str | list[str] | list[dict[str, any]], thread_id: str, model_name: str) -> AsyncGenerator[str, None]:
                
        config = { 'configurable': { 'thread_id': ObjectId(thread_id) } }

        # asStream emits events for every action the agent performs. doesn't wait for end result.
        async for chunk in self.graph.astream(
            input = { 'messages': self.__format_messages(messages=messages), 'model_name': model_name },
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
                and 'role' in messages[0]
                and 'content' in messages[0]
            ):
                result = []
                for msg in messages:
                    if msg['role'] == 'user':
                        result.append(HumanMessage(content=msg['content']))
                    elif msg['role'] == 'assistant':
                        result.append(AIMessage(content=msg['content']))
                return result

            return [HumanMessage(content=message) for message in messages]

        return []
    
    async def regenerate_response(self, thread_id: str) -> AsyncGenerator[str, None]:
        config = { 'configurable': { 'thread_id': ObjectId(thread_id) } }
        state = await self.graph.aget_state(config)
        messages = state.values.get('messages', [])

        if not messages:
            raise ValueError('no history found.')
        
        last_msg = messages[-1]
        
        model = 'fast'
        if last_msg.type == 'ai':
            model = last_msg.additional_kwargs.get('model', 'fast')

        last_human_msg = None
        messages_to_remove = []

        for msg in reversed(messages):
            messages_to_remove.append(RemoveMessage(id=msg.id))
            
            if msg.type == 'human':
                last_human_msg = msg
                break

        if not last_human_msg:
            raise ValueError('no user message found.')

        print(model)

        await self.graph.aupdate_state(config, {"messages": messages_to_remove})

        response_stream = self.get_response(messages=last_human_msg.content, thread_id=thread_id, model_name=model)

        async for chunk in response_stream:
            yield chunk

      