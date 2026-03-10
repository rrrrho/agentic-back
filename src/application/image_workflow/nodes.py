import httpx
from langchain_core.messages import AIMessage

from src.application.image_workflow.chains import get_image_generation_chain, get_translator_chain
from src.domain.image_state import ImageState
from src.domain.state import CustomState
from src.config import settings

def make_translator_node(llm):

    async def translator_node(state: ImageState) -> CustomState:
        translator_chain = get_translator_chain(llm)

        response = await translator_chain.ainvoke(
            {
                'messages': state['messages'],
                'request': state['request']
            }
        )

        print(response)

        return { 'prompt': response.content }
    
    return translator_node

def make_image_generation_node(llm):

    async def image_generation_node(state: ImageState) -> CustomState:
        headers = {
            "Authorization": f"Bearer {settings.OPEN_ROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "google/gemini-2.5-flash-image",
            "messages": [{"role": "user", "content": state['prompt']}],
            "modalities": ["image", "text"] 
        }
        
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )

            data = res.json()
            
        try:
            # image in base64
            image_url = data["choices"][0]["message"]["images"][0]["image_url"]["url"]
        except (KeyError, IndexError):
            image_url = ""

        message = AIMessage(content=f"![Image]({image_url})")

        return { 'messages': [message], 'image_url': image_url }
    
    return image_generation_node