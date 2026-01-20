from src.application.workflow.graph import create_workflow_graph
from src.config import settings
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from langchain_core.tools import BaseTool

def get_compiled_graph(checkpointer: AsyncMongoDBSaver, tools: list[BaseTool]):
    builder = create_workflow_graph(tools)
    return builder.compile(checkpointer=checkpointer)

    