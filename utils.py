from openai import OpenAI
import os

class OpenAIChatResponse:
    def __init__(self, **kwargs):
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI()
    
    def generate_response(self, query:str, model:str = "gpt-3.5-turbo", max_token:int = 4000):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                model=model,
                max_tokens=max_token,
            )
            return chat_completion.choices[0].message.content
        except:
            print('Error generating response')
            return None
    
    def generate_summary(self, text:str, model:str = "gpt-3.5-turbo", max_token:int = 4000):

        query = f"""
                    Please generate a detailed summary of the following text: {text}
                """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                model=model,
                max_tokens=max_token,
            )
            return chat_completion.choices[0].message.content
        except:
            print('Error generating response')
            return None