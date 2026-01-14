from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.config import settings
from src.domain.prompts import PERSONALITY_CARD

def get_chat_model(temperature: float = 0.7, model_name: str = settings.GROQ_LLM_MODEL) -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=model_name,
        temperature=temperature,
    )

def get_response_chain() -> RunnableSequence:
    '''
    injects state variables into prompt template and adds message historial to context

    returns: 
        ChatPromptTemplate
        ChatGroq
    '''
    model = get_chat_model();
    system_message = PERSONALITY_CARD

    prompt = ChatPromptTemplate.from_messages(
        [
            ('system', system_message.prompt),
            MessagesPlaceholder(variable_name='messages')
        ],
        template_format='jinja2'
    )

    # take prompt output and insert it as an input to the model. pipeline ready to use.
    return prompt | model