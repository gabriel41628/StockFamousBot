import requests
from config import MERCADO_PAGO_TOKEN

def criar_pagamento(titulo, valor):
    url = "https://api.mercadopago.com/checkout/preferences"
    headers = {
        "Authorization": f"Bearer {APP_USR-8017733387483580-040117-b163d6c7fcdfb00930f24df53b8501ad-2040475905}",
        "Content-Type": "application/json"
    }
    payload = {
        "items": [{
            "title": titulo,
            "quantity": 1,
            "currency_id": "BRL",
            "unit_price": float(valor)
        }],
        "notification_url": "https://fearless-rebirth-production.up.railway.app/webhook",
        "auto_return": "approved",
        "back_urls": {
            "success": "https://t.me/StockFamous_Bot",
            "failure": "https://t.me/StockFamous_Bot",
            "pending": "https://t.me/StockFamous_Bot"
        }
    }

    try:
        resposta = requests.post(url, json=payload, headers=headers)
        if resposta.ok:
            data = resposta.json()
            return data["init_point"], data["id"]
        else:
            print("⚠️ Erro ao criar pagamento:", resposta.status_code, resposta.text)
            return None, None
    except Exception as e:
        print("❌ Erro inesperado ao criar pagamento:", str(e))
        return None, None
