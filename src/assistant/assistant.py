from typing import TYPE_CHECKING

from enums import TextFormat


if TYPE_CHECKING:
    from mantis.mantis_client import MantisClient

I_HAVE_A_QUESTION = "I have a question: "
NO_CHANGES_NEEDED = "No changes needed"

CONVERSION_PROMPT_TEMPLATE = '''
You are a translation engine for converting {FROM_FORMAT} to {TO_FORMAT}.
If no changes are needed, say '{NO_CHANGES_NEEDED}'.
If you have a question or a request, simply say, '{I_HAVE_A_QUESTION}' followed by your question, then we will raise it to the developers.
Don't make any other comments.
'''.strip()

VERBOSITY_PROMPT_TEMPLATE = f"""
You are a task managing engine for describing Jira tasks.
When you receive a task description, you expand on it.
Make up reasons if you have to.
Make the task sound very important.
Please retain Markdown formatting.
If no changes are needed, say '{NO_CHANGES_NEEDED}'.
If you have a question or a request, simply say, '{I_HAVE_A_QUESTION}' followed by your question, then we will raise it to the developers.
Don't make any other comments.
"""


class Assistant:
    def __init__(self, mantis: 'MantisClient'):
        self.mantis = mantis

    def convert_text_format(self, input_text: str, target_format: TextFormat) -> str:
        if target_format is TextFormat.MARKDOWN:
            FROM_FORMAT = TextFormat.JIRA
            TO_FORMAT = TextFormat.MARKDOWN
        elif target_format is TextFormat.JIRA:
            FROM_FORMAT = TextFormat.MARKDOWN
            TO_FORMAT = TextFormat.JIRA
        else:
            raise ValueError(f'Unrecognized format: {target_format}')

        prompt = CONVERSION_PROMPT_TEMPLATE.format(
            FROM_FORMAT=FROM_FORMAT.value,
            TO_FORMAT=TO_FORMAT.value,
            NO_CHANGES_NEEDED=NO_CHANGES_NEEDED,
            I_HAVE_A_QUESTION=I_HAVE_A_QUESTION
        )
        response = self.mantis.open_ai_client.get_completion(input_text, prompt)
        if response.strip(' ').strip('.') == NO_CHANGES_NEEDED:
            return input_text
        elif response.startswith(I_HAVE_A_QUESTION):
            question = response[len(I_HAVE_A_QUESTION):]
            raise ValueError(f"Question from AI: {question}")
        else:
            return response

    def make_verbose(self, input_text: str) -> str:
        response = self.mantis.open_ai_client.get_completion(input_text, VERBOSITY_PROMPT_TEMPLATE)
        if response.strip(' ').strip('.') == NO_CHANGES_NEEDED:
            return input_text
        elif response.startswith(I_HAVE_A_QUESTION):
            question = response[len(I_HAVE_A_QUESTION):]
            raise ValueError(f"Question from AI: {question}")
        else:
            return response
