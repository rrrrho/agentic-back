from langchain_core.runnables import RunnableConfig

from src.application.workflow.chains import get_response_chain
from src.domain.state import CustomState


async def conversation_node(state: CustomState, config: RunnableConfig) -> CustomState:
    '''
    decides whether to call a tool or to generate a response immediately

    args:
        state: schema of the graph + reducer functions (defines how it is updated). 
        it's like a backpack passed through all nodes and edges.

        config: provides runtime config and context for executin Runnables. 
        it's a dic that cant be passed to methods like invoke, stream, etc., to 
        control various aspects of the execution (tracing, concurrency, etc.).

    returns:
        CustomState: our state which travels through the pipeline.
    '''
    summary = state.get('summary', '')
    conversation_chain = get_response_chain()

    '''
    response example:

    AIMessage(
        content="El alma es inmaterial...", 
        tool_calls=[], 
        response_metadata={'token_usage': 150...}
    )
    '''
    response = await conversation_chain.ainvoke(
        {
            'messages': state['messages'],
            'summary': summary
        },
        config
    )

    # updates list of messages
    return { 'messages': response }