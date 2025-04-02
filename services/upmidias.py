import requests
from config import SMM_API_KEY, SMM_API_URL

def enviar_pedido(service_id, link, quantidade=100):
    payload = {
        "key": SMM_API_KEY,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantidade
    }

    response = requests.post(SMM_API_URL, data=payload)
    try:
        return response.json()
    except Exception as e:
        print("❌ Erro ao enviar pedido:", str(e))
        return {}
