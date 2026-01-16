import uuid
from src.application.workflow.graph import create_workflow_graph
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from typing import Any, AsyncGenerator, Union
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

from src.domain.state import CustomState
from src.config import settings


async def get_response(
    messages: str | list[str] | list[dict[str, any]],
    thread_id: str
) -> AsyncGenerator[str, None]:
    """runs the agent and returns real-time responses, instead of waiting for the text to be fully generated.

    args:
        messages: can be one of:
            - a single string message.
            - a list of string messages.
            - a list of dictionaries with 'role' and 'content' keys.

        returns:
            AsyncGenerator[str, None]: a function that returns tokens as the model generates them.
    """
    graph_builder = create_workflow_graph()

    try:
        async with AsyncMongoDBSaver.from_conn_string(
            conn_string = settings.MONGO_URI,
            db_name = settings.MONGO_DB_NAME,
            checkpoint_collection_name = settings.MONGO_STATE_CHECKPOINT_COLLECTION,
            writes_collection_name = settings.MONGO_STATE_WRITES_COLLECTION
        ) as checkpointer:
            
            graph = graph_builder.compile(checkpointer=checkpointer)

            config = {
                "configurable": { "thread_id": thread_id },
            }

            # asStream emits events for every action the agent performs. doesn't wait for end result.
            async for chunk in graph.astream(
                input = {
                    'messages': __format_messages(messages=messages)
                },
                config = config,
                stream_mode = 'messages'
            ):
                # filters non content (it emits technical events)
                if chunk[1]['langgraph_node'] == 'conversation_node' and isinstance(chunk[0], AIMessageChunk):
                    # sends text fragments until response is fully completed
                    yield chunk[0].content

    except Exception as e:
        raise RuntimeError(f"error running conversation workflow: {str(e)}") from e


def __format_messages(
    messages: Union[str, list[dict[str, Any]]],
    ) -> list[Union[HumanMessage, AIMessage]]:
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


      