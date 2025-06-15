import os

from openai import OpenAI

BASE_URL = "https://ai-gateway.zende.sk/v1" #/chat/completions"
API_KEY = os.environ["CHAT_GPT_KEY"]
I_HAVE_A_QUESTION = "I have a question: "
NO_CHANGES_NEEDED = "No changes needed"

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

def make_verbose(input_text: str) -> str:
  completion = client.chat.completions.create(
    model="gpt-4.1",
    messages=[
      {"role": "developer", "content": (
        "You are a task managing engine for describing Jira tasks. "
            "When you receive a task description, you expand on it. "
            "Make up reasons if you have to. "
            "Make the task sound very important. "
            "Please retain Markdown formatting. "
        f"If no changes are needed, say '{NO_CHANGES_NEEDED}'."
        f"If you have a question or a request, simply say, '{I_HAVE_A_QUESTION}' followed by your question, then we will raise it to the developers."
        "Don't make any other comments.")},
      {"role": "user", "content": input_text}
    ]
  )
  response = completion.choices[0].message.content
  assert response, "Response is empty"
  if response.strip(' ').strip('.') == NO_CHANGES_NEEDED:
    return input_text
  elif response.startswith(I_HAVE_A_QUESTION):
    question = response[len(I_HAVE_A_QUESTION):]
    raise ValueError(f"Question from AI: {question}")
  else:
    return response
