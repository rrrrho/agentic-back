from functools import lru_cache
from langgraph.graph import END, START, StateGraph

from src.application.image_workflow.nodes import make_translator_node
from src.application.image_workflow.nodes import make_image_generation_node
from src.domain.image_state import ImageState

def create_image_workflow_graph(image_generation_llm, translator_llm) -> StateGraph[ImageState]:
    graph_builder = StateGraph(ImageState)

    translator_node = make_translator_node(llm=translator_llm)
    image_generation_node = make_image_generation_node(llm=image_generation_llm)

    # adding nodes
    graph_builder.add_node('translator_node', translator_node)
    graph_builder.add_node('image_generation_node', image_generation_node)

    # defining flow
    graph_builder.add_edge(START, 'translator_node')
    graph_builder.add_edge('translator_node', 'image_generation_node')
    graph_builder.add_edge('image_generation_node', END)
    
    return graph_builder