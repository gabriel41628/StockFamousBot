from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from services.pagamentos import criar_pagamento
from database.models import salvar_pedido, listar_pedidos, cancelar_pedido
from services.pacotes import PACOTES

# Mostra botões organizados por categoria
async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    for categoria, pacotes in PACOTES.items():
        categoria_buttons = []
        for nome in pacotes:
            categoria_buttons.append(
                [InlineKeyboardButton(nome, callback_data=f"comprar:{nome}")]
            )
        keyboard.append([InlineKeyboardButton(f"📦 {categoria}", callback_data="ignore")])
        keyboard.extend(categoria_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha um pacote:", reply_markup=reply_markup)

# Lida com cliques nos botões
async def clique_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("comprar:"):
        return

    nome_pacote = data.split(":", 1)[1]
    pacote = None
    for categoria in PACOTES.values():
        if nome_pacote in categoria:
            pacote = categoria[nome_pacote]
            break

    if not pacote:
        await query.edit_message_text("🚫 Pacote não encontrado.")
        return

    preco = pacote["preco"]
    titulo = nome_pacote
    chat_id = query.message.chat_id
    service_id = pacote.get("id_seguidores") or pacote.get("id")
    quantidade = pacote.get("quantidade", 100)

    link_pagamento, mp_id = criar_pagamento(titulo, preco)

    if not link_pagamento:
        await query.edit_message_text("❌ Erro ao gerar pagamento. Tente novamente mais tarde.")
        return

    salvar_pedido(service_id, chat_id, link_pagamento, mp_id, status="aguardando", quantidade=quantidade)

    await query.edit_message_text(
        f"💸 Pedido criado para *{titulo}*\n"
        f"Preço: R${preco:.2f}\n\n"
        f"Clique no link para pagar:\n{link_pagamento}",
        parse_mode="Markdown"
    )

async def listar_pacotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "📦 *Pacotes disponíveis:*\n\n"
    for categoria, pacotes in PACOTES.items():
        texto += f"*{categoria}:*\n"
        for nome, dados in pacotes.items():
            preco = dados["preco"]
            descricao = dados.get("descricao", "")
            texto += f"• *{nome}* — R${preco:.2f}\n_{descricao}_\n"
        texto += "\n"

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
        "/comprar – Mostra os pacotes disponíveis com botões interativos\n"
        "/status – Ver seus últimos pedidos e o status de cada um\n"
        "/cancelar <id do pagamento> – Cancela um pedido que ainda não foi confirmado\n"
        "/cafe – Uma pausa emocional em formato de comando ☕\n"
        "/ajuda – Você já está aqui, parabéns 👏\n"
        "/contato – Falar com o suporte do bot\n\n"
        "⚠️ Clique nos botões e seja feliz."
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def cafe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "☕ Café sendo preparado...\n"
        "Pronto! Agora você pode debugar bugs com mais moral e menos medo. 🤓"
    )

async def contato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Para falar com o suporte, envie uma mensagem para [@Bielzeramartins](https://t.me/Bielzeramartins)",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

def register_user_handlers(app):
    app.add_handler(CommandHandler("comprar", comprar))
    app.add_handler(CallbackQueryHandler(clique_callback))
    app.add_handler(CommandHandler("pacotes", listar_pacotes))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("cafe", cafe))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("contato", contato))
