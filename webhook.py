from flask import Flask, request
from database.models import atualizar_status
from services.upmidias import enviar_pedido
import sqlite3
import os

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def mercado_pago_webhook():
    data = request.json
    pagamento_id = str(data.get("id"))

    if not pagamento_id:
        return "Sem ID", 200

    conn = sqlite3.connect("dados.db")
    c = conn.cursor()
    c.execute("SELECT id, service_id, link, quantidade FROM pedidos WHERE mp_id = ? AND status = 'aguardando'", (pagamento_id,))
    pedido = c.fetchone()
    conn.close()

    if pedido:
        _, service_id, link, quantidade = pedido
        resposta = enviar_pedido(service_id, link, quantidade)
        fornecedor_id = str(resposta.get("order", "N/A"))
        atualizar_status(pagamento_id, "confirmado", fornecedor_id)
        print(f"✅ Pagamento confirmado. Pedido enviado: {fornecedor_id}")
    else:
        print(f"⚠️ Pagamento {pagamento_id} não encontrado ou já processado.")

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
