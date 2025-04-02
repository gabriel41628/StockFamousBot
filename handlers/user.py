from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from services.pacotes import PACOTES
from services.pagamentos import criar_pagamento
from database.models import salvar_pedido, listar_pedidos, cancelar_pedido

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

    salvar_pedido(service_id, chat_id, link_pagamento, mp_id, status="aguardando")

    await update.message.reply_text(
        f"💸 Pedido criado para *{titulo}*\n"
        f"Preço: R${preco:.2f}\n\n"
        f"Clique no link para pagar:\n{link_pagamento}",
        parse_mode="Markdown"
    )

async def listar_pacotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "📦 *Pacotes disponíveis:*\n\n"
    for nome, dados in PACOTES.items():
        preco = dados["preco"]
        descricao = dados.get("descricao", "")
        texto += f"*{nome}* — R${preco:.2f}\n_{descricao}_\n\n"

    await update.message.reply_text(texto, parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pedidos = listar_pedidos()
    chat_id = update.message.chat_id

    resposta = "📊 *Seus últimos pedidos:*\n\n"
    encontrados = False

    for p in pedidos:
        if p[1] == chat_id:
            encontrados = True
            resposta += f"📦 *{p[2]}*\n💰 R${p[4]:.2f}\n🔗 [Link]({p[3]})\n📌 Status: `{p[5]}`\n\n"

    if not encontrados:
        resposta = "Você ainda não tem pedidos registrados."

    await update.message.reply_text(resposta, parse_mode="Markdown")

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Use assim: /cancelar <ID do pagamento>")
        return

    mp_id = context.args[0]
    chat_id = update.message.chat_id
    cancelar_pedido(mp_id, chat_id)

    await update.message.reply_text("❌ Pedido cancelado com sucesso (ou ele já estava cancelado mesmo).")

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📌 *Como usar o Stock Famous Bot:*\n\n"
        "/pacotes – Lista todos os pacotes disponíveis com preços e descrições\n"
        "/comprar <nome do pacote> – Inicia a compra de um pacote\n"
        "/status – Ver seus últimos pedidos e o status de cada um\n"
        "/cancelar <id do pagamento> – Cancela um pedido que ainda não foi confirmado\n"
        "/cafe – Uma pausa emocional em formato de comando ☕\n"
        "/ajuda – Você já está aqui, parabéns 👏\n\n"
        "⚠️ Digite o nome do pacote exatamente como aparece na lista!\n"
        "Dúvidas? Chama no suporte humano.\n\n"
        "Feito com bytes e cafeína. ☕"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def cafe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "☕ Café sendo preparado...\n"
        "Pronto! Agora você pode debugar bugs com mais moral e menos medo. 🤓"
    )

def register_user_handlers(app):
    app.add_handler(CommandHandler("comprar", comprar))
    app.add_handler(CommandHandler("pacotes", listar_pacotes))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("cafe", cafe))
    app.add_handler(CommandHandler("cancelar", cancelar))
