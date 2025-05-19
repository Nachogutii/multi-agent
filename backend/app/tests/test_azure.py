# test_azure.py
from backend.app.services.azure_openai import AzureOpenAIClient

def test_azure_connection():
    client = AzureOpenAIClient()
    
    # Prueba básica
    response = client.get_response(
        system_prompt="You are a helpful assistant",
        user_prompt="What is the capital of France?"
    )
    print("Respuesta básica:", response)
    
    # Prueba con un deployment específico
    response = client.get_response(
        system_prompt="You are a helpful assistant",
        user_prompt="What is the capital of Spain?",
        deployment="gpt-4o-mini"  # o el nombre de tu deployment
    )
    print("Respuesta con deployment específico:", response)

if __name__ == "__main__":
    test_azure_connection()