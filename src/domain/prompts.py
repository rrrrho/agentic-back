class Prompt:
    def __init__(self, name: str, prompt: str) -> None:
        self.name = name
        self.prompt = prompt


# character
__CHARACTER_CARD = """

"""

CHARACTER_CARD = Prompt(
    name='custom_card',
    prompt=__CHARACTER_CARD
)

# summary
__SUMMARY_PROMPT = """Create a summary of the conversation between you and the user.
The summary must be a short description of the conversation so far, but that also captures all the
relevant information shared between you and the user: """

SUMMARY_PROMPT = Prompt(
    name="summary_prompt",
    prompt=__SUMMARY_PROMPT,
)
