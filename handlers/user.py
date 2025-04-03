from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from services.pagamentos import criar_pagamento
from database.models import (
    salvar_pedido_completo,
    listar_pedidos,
    cancelar_pedido
)
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
    keyboard = [
        [InlineKeyboardButton(f"📦 {categoria}", callback_data=f"categoria:{categoria}")]
        for categoria in PACOTES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha uma categoria de pacotes:", reply_markup=reply_markup)

async def clique_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

    if data == "menu":
        await comprar(update, context)
        return

    if data.startswith("categoria:"):
        categoria = data.split(":", 1)[1]
        pacotes = PACOTES.get(categoria)

        if not pacotes:
            await query.edit_message_text("🚫 Nenhum pacote encontrado para essa categoria.")
            return

        keyboard = [
            [InlineKeyboardButton(f"{nome} - R${dados['preco']:.2f}", callback_data=f"pacote:{categoria}:{nome}")]
            for nome, dados in pacotes.items()
        ]
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"📦 Pacotes disponíveis para *{categoria}*:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif data.startswith("pacote:"):
        _, categoria, nome_pacote = data.split(":", 2)
        pacote = PACOTES.get(categoria, {}).get(nome_pacote)

        if not pacote:
            await query.edit_message_text("🚫 Pacote não encontrado.")
            return

        pending_orders[chat_id] = {
            "categoria": categoria,
            "pacote": nome_pacote,
            "dados": pacote
        }

        preco = pacote["preco"]
        await query.edit_message_text(
            f"🗓️ Você escolheu o pacote *{nome_pacote}*\n"
            f"💲 Valor: *R${preco:.2f}*\n"
            "\nEnvie agora o link ou @usuario para continuar.",
            parse_mode="Markdown"
        )

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
            await update.message.reply_text("⚠️ Isso não parece um @usuario ou um link válido.")
            return
    else:
        if not entrada.startswith("http"):
            await update.message.reply_text("⚠️ Link inválido. Comece com http.")
            return

    preco = pacote["preco"]
    service_id = pacote["id"]

    link_pagamento, mp_id = criar_pagamento(pacote_nome, preco)

    if not link_pagamento:
        await update.message.reply_text("❌ Erro ao gerar pagamento.")
        return

    salvar_pedido_completo(
        usuario=chat_id,
        servico=pacote_nome,
        link=entrada,
        preco=preco,
        status="aguardando",
        mp_id=mp_id,
        fornecedor_id=None,
        service_id=service_id,
        chat_id=chat_id
    )

    await update.message.reply_text(
        f"✅ Pedido criado!\n\n"
        f"Produto: *{pacote_nome}*\n"
        f"Valor: R${preco:.2f}\n"
        f"🔗 Link enviado: {entrada}\n\n"
        f"💳 Clique aqui para pagar:\n{link_pagamento}",
        parse_mode="Markdown"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pedidos = listar_pedidos()
    chat_id = update.message.chat_id

    resposta = "📊 *Seus últimos pedidos:*\n\n"
    encontrados = False

    for p in pedidos:
        if p[9] == chat_id:
            encontrados = True
            resposta += (
                f"📦 *{p[2]}*\n"
                f"💰 R${p[4]:.2f}\n"
                f"🔗 [Link]({p[3]})\n"
                f"📌 Status: `{p[5]}`\n\n"
            )

    if not encontrados:
        resposta = "❌ Nenhum pedido encontrado."

    await update.message.reply_text(resposta, parse_mode="Markdown")

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Use assim: /cancelar <ID do pagamento>")
        return

    mp_id = context.args[0]
    chat_id = update.message.chat_id
    cancelar_pedido(mp_id, chat_id)

    await update.message.reply_text("❌ Pedido cancelado com sucesso.")

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📌 *Como usar o Stock Famous Bot:*\n\n"
        "/start – Início\n"
        "/comprar – Começar uma compra\n"
        "/status – Ver seus pedidos\n"
        "/cancelar <id> – Cancelar pedido\n"
        "/ajuda – Ajuda\n"
        "/contato – Suporte"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def contato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Suporte: [@Bielzeramartins](https://t.me/Bielzeramartins)",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

def register_user_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comprar", comprar))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("contato", contato))
    app.add_handler(CallbackQueryHandler(clique_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_link))
