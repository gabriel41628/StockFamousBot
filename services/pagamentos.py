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
        "notification_url": "https://SUASEGURL/webhook",  # coloque uma URL real se tiver
        "back_urls": {
            "success": "https://t.me/StockFamous_Bot",
            "failure": "https://t.me/StockFamous_Bot",
            "pending": "https://t.me/StockFamous_Bot"
        },
        "auto_return": "approved"
    }

    try:
        resposta = requests.post(url, json=payload, headers=headers)
        if resposta.ok:
            data = resposta.json()
            return data["init_point"], data["id"]
        else:
            print("Erro Mercado Pago:", resposta.text)
            return None, None
    except Exception as e:
        print("Erro inesperado:", e)
        return None, None
