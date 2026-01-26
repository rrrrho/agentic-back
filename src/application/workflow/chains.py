from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.domain.prompts import CONTEXT_SUMMARY_PROMPT, EXTEND_SUMMARY_PROMPT, PERSONALITY_CARD, SUMMARY_PROMPT

def get_response_chain(llm, tools: list) -> RunnableSequence:
    '''
    injects state variables into prompt template and adds message historial to context

    returns: 
        ChatPromptTemplate
        ChatGroq
    '''

    llm_with_tools = llm.bind_tools(tools)
    system_message = PERSONALITY_CARD

    prompt = ChatPromptTemplate.from_messages(
        [
            ('system', system_message.prompt),
            MessagesPlaceholder(variable_name='messages')
        ],
        template_format='jinja2'
    )

    # take prompt output and insert it as an input to the model. pipeline ready to use.
    return prompt | llm_with_tools

def get_conversation_summary_chain(llm, summary: str = '') -> RunnableSequence:

    summary_message = EXTEND_SUMMARY_PROMPT if summary else SUMMARY_PROMPT

    prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name='messages'),
            ('human', summary_message.prompt)
        ],
        template_format='jinja2'
    )

    return prompt | llm

def get_context_summary_chain(llm):

    prompt = ChatPromptTemplate.from_messages(
        [
            ("human", CONTEXT_SUMMARY_PROMPT.prompt),
        ],
        template_format="jinja2",
    )

    return prompt | llm