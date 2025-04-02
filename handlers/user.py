from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from services.pacotes import PACOTES
from services.pagamentos import criar_pagamento
from database.models import salvar_pedido

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Use assim: /comprar <nome do pacote>")
        return

    nome_pacote = " ".join(context.args)
    pacote = PACOTES.get(nome_pacote)

    if not pacote:
        await update.message.reply_text("🚫 Pacote não encontrado. Use /pacotes para ver a lista.")
        return

    preco = pacote["preco"]
    titulo = nome_pacote
    chat_id = update.message.chat_id
    service_id = pacote.get("id_seguidores") or pacote.get("id")
    quantidade = pacote.get("quantidade", 100)

    link_pagamento, mp_id = criar_pagamento(titulo, preco)

    if not link_pagamento:
        await update.message.reply_text("❌ Erro ao gerar pagamento. Tente novamente mais tarde.")
        return

    salvar_pedido(service_id, chat_id, link_pagamento, mp_id, status="aguardando", quantidade=quantidade)

    await update.message.reply_text(
        f"💸 Pedido criado para *{titulo}*\n"
        f"Preço: R${preco:.2f}\n\n"
        f"Clique no link para pagar:\n{link_pagamento}",
        parse_mode="Markdown"
    )

def register_user_handlers(app):
    app.add_handler(CommandHandler("comprar", comprar))
