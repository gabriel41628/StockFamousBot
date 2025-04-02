from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from services.pagamentos import criar_pagamento
from database.models import salvar_pedido, listar_pedidos, cancelar_pedido
from services.pacotes import PACOTES

# 🟢 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "👋 *Bem-vindo ao Stock Famous Bot!*\n\n"
        "Aqui você pode turbinar seu perfil com seguidores, curtidas e visualizações. "
        "Tudo com pagamento via Mercado Pago e entrega automática.\n\n"
        "🛒 Use /comprar para iniciar sua compra.\n"
        "📦 Use /pacotes para ver os pacotes disponíveis.\n"
        "📊 Use /status para acompanhar seus pedidos.\n"
        "❓ Use /ajuda para ver todos os comandos."
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

# 🛒 /comprar - mostra categorias
async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for categoria in PACOTES:
        keyboard.append([InlineKeyboardButton(f"📦 {categoria}", callback_data=f"categoria:{categoria}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha uma categoria de pacotes:", reply_markup=reply_markup)

# 🔁 Botões e navegação
async def clique_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Escolheu uma categoria
    if data.startswith("categoria:"):
        categoria = data.split(":", 1)[1]
        pacotes = PACOTES.get(categoria, {})
        keyboard = [
            [InlineKeyboardButton(nome, callback_data=f"comprar:{categoria}:{nome}")]
            for nome in pacotes
        ]
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu")])
        await query.edit_message_text(
            f"🛍️ *{categoria}*\nSelecione um pacote:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Escolheu um pacote
    if data.startswith("comprar:"):
        _, categoria, nome_pacote = data.split(":", 2)
        pacote = PACOTES.get(categoria, {}).get(nome_pacote)
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
            await query.edit_message_text("❌ Erro ao gerar pagamento.")
            return

        salvar_pedido(service_id, chat_id, link_pagamento, mp_id, status="aguardando", quantidade=quantidade)

        await query.edit_message_text(
            f"💸 Pedido criado para *{titulo}*\n"
            f"Preço: R${preco:.2f}\n\n"
            f"🔗 [Clique aqui para pagar]({link_pagamento})",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        return

    # Voltar para o menu de categorias
    if data == "voltar_menu":
        keyboard = []
        for categoria in PACOTES:
            keyboard.append([InlineKeyboardButton(f"📦 {categoria}", callback_data=f"categoria:{categoria}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Escolha uma categoria de pacotes:",
            reply_markup=reply_markup
        )

# /pacotes - lista completa
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

# /status
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

# /cancelar
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Use assim: /cancelar <ID do pagamento>")
        return
    mp_id = context.args[0]
    chat_id = update.message.chat_id
    cancelar_pedido(mp_id, chat_id)
    await update.message.reply_text("❌ Pedido cancelado com sucesso (ou já estava cancelado).")

# /ajuda
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📌 *Como usar o Stock Famous Bot:*\n\n"
        "/start – Ver mensagem de boas-vindas\n"
        "/comprar – Iniciar compra com menus e botões\n"
        "/pacotes – Ver lista de todos os pacotes disponíveis\n"
        "/status – Ver seus últimos pedidos\n"
        "/cancelar <id> – Cancelar pedido pendente\n"
        "/cafe – Você merece\n"
        "/contato – Suporte humano (quase)\n"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

# /cafe
async def cafe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("☕ Uma pausa com café... e dignidade. Volte logo!")

# /contato
async def contato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Fale com o suporte: [@Bielzeramartins](https://t.me/Bielzeramartins)",
        parse_mode="Markdown", disable_web_page_preview=True
    )

# Handlers
def register_user_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comprar", comprar))
    app.add_handler(CallbackQueryHandler(clique_callback))
    app.add_handler(CommandHandler("pacotes", listar_pacotes))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("cafe", cafe))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("contato", contato))
