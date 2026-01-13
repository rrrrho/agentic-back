from functools import lru_cache
from langgraph.graph import END, START, StateGraph

from src.application.workflow.nodes import conversation_node
from src.domain.state import CustomState

@lru_cache(maxsize=1)
def create_workflow_graph() -> StateGraph[CustomState]:
    '''
    creates the decision graph.

    returns:
        StateGraph[CustomState]: class where the state, nodes and edges of the graph are defined, before it is compiled.
    '''
    graph_builder = StateGraph(CustomState);

    # adding nodes
    graph_builder.add_node('conversation_node', conversation_node)


    # defining flow
    graph_builder.add_edge(START, 'conversation_node')
    graph_builder.add_edge('conversation_node', END)

    return graph_builder