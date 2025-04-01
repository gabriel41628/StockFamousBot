import requests
from config import MERCADO_PAGO_TOKEN

def criar_pagamento(titulo, valor):
    url = "https://api.mercadopago.com/checkout/preferences"
    headers = {
        "Authorization": f"Bearer {MERCADO_PAGO_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "items": [{
            "title": titulo,
            "quantity": 1,
            "currency_id": "BRL",
            "unit_price": float(valor)
        }],
        "notification_url": "https://SEU_NGROK/webhook",  # atualize isso depois
        "auto_return": "approved"
    }

    resposta = requests.post(url, json=payload, headers=headers)

    try:
        return resposta.json()["init_point"], resposta.json()["id"]
    except Exception as e:
        print("Erro ao criar pagamento:", resposta.text)
        return None, None
