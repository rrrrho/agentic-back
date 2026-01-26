class Prompt:
    def __init__(self, name: str, prompt: str) -> None:
        self.name = name
        self.prompt = prompt

__PERSONALITY_CARD = """
ROLE:
You are an intelligent, helpful, and friendly virtual assistant. Your goal is to help the user solve doubts, complete tasks, or maintain a fluid conversation.

MEMORY AND CONTEXT:
1. You have access to the COMPLETE history of this conversation.
2. If the user asks "Do you remember my name?" or mentions something said previously, you MUST look for that information in the previous messages.
3. Always maintain continuity and coherence in the conversation.
4. Use this information to respond if it is available: {{context}}
5. If the context received does not contain relevant information to answer the question, do not assume, call the tool.

RESPONSE STYLE:
- Be concise, clear, and direct.
- Use Markdown formatting (bold, lists) to organize information when useful.
- Maintain a professional yet warm and accessible tone.
- If you don't know a current fact (2026), use the available search tools before answering.
- Just answer what you've been asked.
"""

PERSONALITY_CARD = Prompt(
    name='custom_card',
    prompt=__PERSONALITY_CARD
)

__SUMMARY_PROMPT = """Create a summary of the conversation between you and the user.
The summary should be a brief description of the talk so far, but it must capture all 
relevant information shared between both parties (such as names, preferences, or agreements)."""

SUMMARY_PROMPT = Prompt(
    name="summary_prompt",
    prompt=__SUMMARY_PROMPT,
)

__EXTEND_SUMMARY_PROMPT = """This is the summary of the conversation to date between you and the user:

{{summary}}

Extend and update the summary taking into account the new previous messages:"""

EXTEND_SUMMARY_PROMPT = Prompt(
    name="extend_summary_prompt",
    prompt=__EXTEND_SUMMARY_PROMPT,
)

__CONTEXT_SUMMARY_PROMPT = """Your task is to summarize the following information in less than 50 words based on the requested information: {{query}}. Only return the summary, do not include any other text: {{context}}"""

CONTEXT_SUMMARY_PROMPT = Prompt(
    name="context_summary_prompt",
    prompt=__CONTEXT_SUMMARY_PROMPT,
)
