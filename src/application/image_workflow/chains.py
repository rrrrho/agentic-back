from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableSequence

from src.domain.prompts import TRANSLATOR_PROMPT


def get_translator_chain(llm) -> RunnableSequence:

    prompt = ChatPromptTemplate.from_messages(
        [
            ('system', TRANSLATOR_PROMPT.prompt),
            MessagesPlaceholder(variable_name='messages')
        ],
        template_format='jinja2'
    )

    return prompt | llm

def get_image_generation_chain(llm):

    prompt = PromptTemplate.from_messages('{prompt}')

    return prompt | llm