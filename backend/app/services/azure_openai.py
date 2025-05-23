from openai import AzureOpenAI
import os
from dotenv import load_dotenv

class AzureOpenAIClient:
    def __init__(self):
        load_dotenv()
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.environ.get("AZURE_OPENAI_KEY")
        self.deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        try:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version="2024-02-15-preview"
            )
        except Exception as e:
            print(f"Error initializing Azure OpenAI client: {str(e)}")
            raise

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

        try:
            response = self.client.chat.completions.create(
                model=deployment,
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
                temperature=1
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error getting response from Azure OpenAI: {str(e)}")
            return "Lo siento, hubo un error al procesar tu solicitud."

# Usage example
if __name__ == "__main__":
    client = AzureOpenAIClient()
    response = client.get_response(
        system_prompt="you are a helpful assistant",
        user_prompt="hello world"
    )
    print(response)