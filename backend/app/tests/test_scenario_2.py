import requests

BACKEND_URL = "http://localhost:8000"


def test_scenario_2():
    print("\n=== TEST: Escenario 2 ===")
    # 1. Reset con id=2
    resp = requests.post(f"{BACKEND_URL}/api/reset", json={"id": 2})
    print("Reset response:", resp.json())

    # 2. Enviar un mensaje de prueba
    msg = {"text": "Hola, ¿en qué puedo ayudarte?"}
    chat_resp = requests.post(f"{BACKEND_URL}/api/chat", json=msg)
    print("Chat response:", chat_resp.json())

if __name__ == "__main__":
    test_scenario_2() 