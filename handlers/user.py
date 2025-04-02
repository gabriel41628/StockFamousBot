from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from services.pagamentos import criar_pagamento
from database.models import salvar_pedido, listar_pedidos, cancelar_pedido
from services.pacotes_data import PACOTES

pending_orders = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚀 Ver Pacotes", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Bem-vindo ao *Stock Famous Bot*!\n\n"
        "Aqui você pode comprar seguidores, curtidas, visualizações e muito mais.\n\n"
        "Use o botão abaixo para começar sua jornada rumo à fama digital!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for categoria in PACOTES:
        keyboard.append([InlineKeyboardButton(f"📦 {categoria}", callback_data=f"categoria:{categoria}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha uma categoria de pacotes:", reply_markup=reply_markup)

async def clique_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = query.message.chat_id

    if data.startswith("categoria:"):
        categoria = data.split(":", 1)[1]
        pacotes = PACOTES.get(categoria, {})

        keyboard = [
            [InlineKeyboardButton(f"{nome} - R${pacote['preco']:.2f}", callback_data=f"pacote:{categoria}:{nome}")]
            for nome, pacote in pacotes.items()
        ]
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Pacotes disponíveis para *{categoria}*:", reply_markup=reply_markup, parse_mode="Markdown")

    elif data.startswith("pacote:"):
        _, categoria, nome_pacote = data.split(":", 2)
        pacote = PACOTES.get(categoria, {}).get(nome_pacote)

        if not pacote:
            await query.edit_message_text("🚫 Pacote não encontrado.")
            return

        pending_orders[chat_id] = {"categoria": categoria, "pacote": nome_pacote, "dados": pacote}

        preco = pacote["preco"]
        await query.edit_message_text(
            f"📅 Você escolheu o pacote *{nome_pacote}*\n"
            f"
💲 Valor: *R${preco:.2f}*\n"
            "\nEnvie agora o link ou @usuario para continuar.",
            parse_mode="Markdown"
        )

    elif data == "menu":
        await comprar(update, context)

async def receber_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in pending_orders:
        return

    entrada = update.message.text.strip()
    dados = pending_orders.pop(chat_id)
    categoria = dados["categoria"]
    pacote_nome = dados["pacote"]
    pacote = dados["dados"]

    if categoria.startswith("Seguidores"):
        if not (entrada.startswith("@") or "instagram.com" in entrada):
            await update.message.reply_text("⚠️ Isso não parece ser um @usuario ou um link válido do Instagram. Tenta de novo com carinho!")
            return
    else:
        if not entrada.startswith("http"):
            await update.message.reply_text("⚠️ Opa! Isso não parece um link válido. Tenta de novo com um link começando com http.")
            return

    preco = pacote["preco"]
    titulo = pacote_nome
    quantidade = pacote.get("quantidade", 100)
    service_id = pacote.get("id_seguidores") or pacote.get("id")

    link_pagamento, mp_id = criar_pagamento(titulo, preco)

    if not link_pagamento:
        await update.message.reply_text("❌ Erro ao gerar pagamento. Tente novamente mais tarde.")
        return

    salvar_pedido(service_id, chat_id, entrada, mp_id, status="aguardando", quantidade=quantidade)

    await update.message.reply_text(
        f"✅ Pedido criado com sucesso!\n"
        f"Produto: *{titulo}*\n"
        f"Valor: R${preco:.2f}\n"
        f"🔗 Link enviado: {entrada}\n\n"
        f"Clique aqui para pagar: {link_pagamento}",
        parse_mode="Markdown"
    )
