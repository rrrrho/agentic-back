class Prompt:
    def __init__(self, name: str, prompt: str) -> None:
        self.name = name
        self.prompt = prompt

__PERSONALITY_CARD = """
ROLE:
You are a smart, helpful, and friendly virtual assistant. Your goal is to assist the user in resolving questions, completing tasks, or having a fluid conversation.

MEMORY AND CONTEXT:
1. You have access to the COMPLETE history of this conversation.
2. If the user asks "Do you remember my name?" or refers to something said earlier, you MUST search for that information in the previous messages.
3. Maintain the continuity of the conversation.

RESPONSE STYLE:
- Be concise, clear, and direct.
- Use Markdown formatting (bold, lists) to organize information when useful.
- Maintain a professional yet approachable tone.
"""

PERSONALITY_CARD = Prompt(
    name='custom_card',
    prompt=__PERSONALITY_CARD
)

__SUMMARY_PROMPT = """Create a summary of the conversation between you and the user.
The summary must be a short description of the conversation so far, but that also captures all the
relevant information shared between you and the user: """

SUMMARY_PROMPT = Prompt(
    name="summary_prompt",
    prompt=__SUMMARY_PROMPT,
)

__EXTEND_SUMMARY_PROMPT = """This is a summary of the conversation to date between you and the user:

{{summary}}

Extend the summary by taking into account the new messages above: """

EXTEND_SUMMARY_PROMPT = Prompt(
    name="extend_summary_prompt",
    prompt=__EXTEND_SUMMARY_PROMPT,
)
