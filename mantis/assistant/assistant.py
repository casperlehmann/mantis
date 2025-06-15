from enum import Enum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient

I_HAVE_A_QUESTION = "I have a question: "
NO_CHANGES_NEEDED = "No changes needed"

CONVERSION_PROMPT_TEMPLATE = '''
You are a translation engine for converting {FROM_FORMAT} to {TO_FORMAT}.
If no changes are needed, say '{NO_CHANGES_NEEDED}'.
If you have a question or a request, simply say, '{I_HAVE_A_QUESTION}' followed by your question, then we will raise it to the developers.
Don't make any other comments.
'''.strip()

class TextFormat(Enum):
    JIRA = "Jira format"
    MARKDOWN = "Markdown"


class Assistant:
    def __init__(self, jira_client: 'JiraClient'):
        self.jira_client = jira_client
        self.TextFormat = TextFormat

    def convert_text_format(self, input_text: str, target_format: TextFormat) -> str:
        if target_format == TextFormat.MARKDOWN:
            FROM_FORMAT = TextFormat.JIRA
            TO_FORMAT = TextFormat.MARKDOWN
        else:
            FROM_FORMAT = TextFormat.MARKDOWN
            TO_FORMAT = TextFormat.JIRA


        prompt = CONVERSION_PROMPT_TEMPLATE.format(
            FROM_FORMAT=FROM_FORMAT.value,
            TO_FORMAT=TO_FORMAT.value,
            NO_CHANGES_NEEDED=NO_CHANGES_NEEDED,
            I_HAVE_A_QUESTION=I_HAVE_A_QUESTION
        )
        response = self.jira_client.open_ai_client.get_completion(input_text, prompt)
        if response.strip(' ').strip('.') == NO_CHANGES_NEEDED:
            return input_text
        elif response.startswith(I_HAVE_A_QUESTION):
            question = response[len(I_HAVE_A_QUESTION):]
            raise ValueError(f"Question from AI: {question}")
        else:
            return response
