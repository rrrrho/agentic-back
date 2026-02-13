from src.application.workflow.graph import create_workflow_graph
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from langchain_core.tools import BaseTool

def get_compiled_graph(checkpointer: AsyncMongoDBSaver, tools: list[BaseTool], llm, poor_llm):
    builder = create_workflow_graph(tools=tools, llm=llm, poor_llm=poor_llm)
    return builder.compile(checkpointer=checkpointer)

    