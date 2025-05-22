from openai import AzureOpenAI
import os
from dotenv import load_dotenv

class AzureOpenAIClient:
    def __init__(self):
        load_dotenv()
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.environ.get("AZURE_OPENAI_KEY")
        self.deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_version="2024-02-15-preview",  # Make sure to use the correct version
            api_key=self.api_key
        )

    def get_response(self, system_prompt, user_prompt, deployment=None):
        """
        Gets a response from Azure OpenAI
        
        Args:
            system_prompt (str): The system prompt
            user_prompt (str): The user prompt
            deployment (str, optional): Name of the deployment to use. If None, uses the default
            
        Returns:
            str: The model's response
        """
        if deployment is None:
            deployment = self.deployment

        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            max_tokens=500,
            temperature=1,
            model=deployment
        )
        return response.choices[0].message.content

# Usage example
if __name__ == "__main__":
    client = AzureOpenAIClient()
    response = client.get_response(
        system_prompt="you are a helpful assistant",
        user_prompt="hello world"
    )
    print(response)