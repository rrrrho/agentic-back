from langchain_core.runnables import RunnableConfig
from langchain_core.messages import RemoveMessage
from langgraph.prebuilt import ToolNode
from langchain_core.tools import BaseTool

from src.application.workflow.chains import get_context_summary_chain, get_conversation_summary_chain, get_response_chain
from src.domain.state import CustomState
from src.config import settings

def make_retriever_node(tools: list[BaseTool]):
    return ToolNode(tools)

def make_conversation_node(llm, tools: list[BaseTool]):

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
        context = state.get('context', '')
        conversation_chain = get_response_chain(llm, tools=tools)

        print(context)
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
                'summary': summary,
                'context': context 
            },
            config
        )


        # updates list of messages
        return { 'messages': response }
    
    return conversation_node

def make_summarize_conversation_node(llm):

    async def summarize_conversation_node(state: CustomState) -> CustomState:
        summary = state.get('summary', '')
        summarize_conversation_chain = get_conversation_summary_chain(llm, summary)

        response = await summarize_conversation_chain.ainvoke(
            {
                'messages': state['messages'],
                'summary': summary
            }
        )

        delete_messages = [
            RemoveMessage(id=m.id)
            for m in state['messages'][: -settings.TOTAL_MESSAGES_AFTER_SUMMARY]
        ]

        return { 'summary': response.content, 'messages': delete_messages }
    
    return summarize_conversation_node

def make_context_summary_node(llm):

    async def context_summary_node(state: CustomState) -> CustomState:
        context_summary_chain = get_context_summary_chain(llm)

        user_query = next(
            (m.content for m in reversed(state['messages']) if m.type == 'human'), 
            "información general"
        )

        response = await context_summary_chain.ainvoke(
            {
                'query': user_query,
                'context': state['messages'][-1].content,
            }
        )

        return { 'context': response.content }
    
    return context_summary_node

async def connector_node(state: CustomState):
    return {}