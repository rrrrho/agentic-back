from langchain_core.runnables import RunnableConfig
from langchain_core.messages import RemoveMessage
from langgraph.prebuilt import ToolNode
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.application.workflow.chains import get_context_summary_chain, get_context_validation_chain, get_conversation_summary_chain, get_response_chain, get_router_chain
from src.domain.state import CustomState
from src.config import settings

def make_retriever_node(tools: list[BaseTool]):
    return ToolNode(tools)

def make_router_node(llm, tools: list[BaseTool]):

    async def router_node(state: CustomState, config: RunnableConfig) -> CustomState:
        retries = state.get('retry_count', 0)
        user_query = state.get('user_query', '')
        messages = state['messages']

        if not user_query:
            user_query = next(
                (m.content for m in reversed(state['messages']) if m.type == 'human'), 
                "información general"
            )

        tool_iterations = 0
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            
            if isinstance(msg, HumanMessage):
                break
                
            if isinstance(msg, AIMessage) and msg.tool_calls:
                tool_iterations += 1

        if tool_iterations >= settings.MAX_TOP_ITERATIONS:
            fallback_message = AIMessage(
                content='I have gathered enough information (tool limit reached). I will now respond.'
            )

            return {
                'messages': fallback_message,
                'user_query': user_query,
                'retry_count': 0
            }

        router_chain = get_router_chain(llm, tools=tools)

        response = await router_chain.ainvoke(
            {
                'messages': state['messages'],
                'user_query': user_query,
                'retry_count': retries
            },
            config
        )

        return { 'user_query': user_query }
    
    return router_node

def make_context_validation_node(llm):

    async def context_validation_node(state: CustomState) -> CustomState:
        context = state['messages'][-1].content
        RemoveMessage(id=state['messages'][-1].id)

        retry_count = state.get('retry_count', 0)
        user_query = state['user_query']

        context_validation_chain = get_context_validation_chain(llm)

        response = await context_validation_chain.ainvoke(
            {
                'messages': state['messages'],
                'user_query': user_query,
                'context': context
            }
        )

        print('\nVALIDATION: ', response.content, '\n')

        retries = retry_count + 1 if response.content == 'FAILED' else retry_count

        return { 'validation_status': response.content, 'retry_count': retries, 'context': context }
    
    return context_validation_node


def make_conversation_node(llm):

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
        conversation_chain = get_response_chain(llm)

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

        print(state['messages'])
        # updates list of messages
        return { 'messages': response, 'user_query': '', 'context': '' }
    
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
        context = state['context']
        context_summary_chain = get_context_summary_chain(llm)
        user_query = state['user_query']

        response = await context_summary_chain.ainvoke(
            {
                'query': user_query,
                'context': context,
            }
        )

        return { 'context': response.content }
    
    return context_summary_node

async def connector_node(state: CustomState):
    return {}