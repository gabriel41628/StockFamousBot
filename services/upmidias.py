import requests
from config import SMM_API_KEY, SMM_API_URL

def enviar_pedido(service_id, link, quantidade=1000):
    payload = {
        "key": SMM_API_KEY,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantidade
    }
    response = requests.post(SMM_API_URL, data=payload)
    return response.json()
