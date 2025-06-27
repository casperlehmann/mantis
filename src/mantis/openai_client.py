from typing import TYPE_CHECKING

from openai import OpenAI


if TYPE_CHECKING:
    from mantis.mantis_client import MantisClient


class OpenAIClient:
    def __init__(self, mantis: 'MantisClient') -> None:
        self.mantis = mantis
        self.disabled = not self.mantis.options.chat_gpt_activated
        self.open_ai = OpenAI(base_url=self.mantis.options.chat_gpt_base_url, api_key=self.mantis.options.chat_gpt_api_key)
        
    def get_completion(self, input_text: str, prompt: str, model: str = 'gpt-4.1') -> str:
        if self.disabled:
            raise ConnectionError('OpenAI connectivity has not been configured')
        completion = self.open_ai.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "developer", "content": prompt},
                    {"role": "user", "content": input_text}
                ]
            )
        response = completion.choices[0].message.content
        if not response:
            raise ValueError("Response is empty")
        return response
