from functools import lru_cache
from langgraph.graph import END, START, StateGraph

from src.application.workflow.edges import should_summarize_conversation
from src.application.workflow.nodes import connector_node, make_conversation_node, make_retriever_node, summarize_conversation_node
from src.domain.state import CustomState
from langgraph.prebuilt import tools_condition
from langchain_core.tools import BaseTool

def create_workflow_graph(tools: list[BaseTool]) -> StateGraph[CustomState]:
    '''
    creates the decision graph.

    returns:
        StateGraph[CustomState]: class where the state, nodes and edges of the graph are defined, before it is compiled.
    '''
    graph_builder = StateGraph(CustomState);
    retriever_node = make_retriever_node(tools=tools)
    conversation_node = make_conversation_node(tools=tools)

    # adding nodes
    graph_builder.add_node('conversation_node', conversation_node)
    graph_builder.add_node('retriever_node', retriever_node)
    graph_builder.add_node('summarize_conversation_node', summarize_conversation_node)
    graph_builder.add_node('connector_node', connector_node)

    # defining flow
    graph_builder.add_edge(START, 'conversation_node')
    graph_builder.add_conditional_edges(
        'conversation_node',
        tools_condition,
        {
            'tools': 'retriever_node',
            END: 'connector_node'
        }
    )
    graph_builder.add_edge('retriever_node', 'conversation_node')
    graph_builder.add_conditional_edges('connector_node', should_summarize_conversation)
    graph_builder.add_edge('summarize_conversation_node', END)

    return graph_builder