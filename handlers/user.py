from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from services.pagamentos import criar_pagamento
from database.models import salvar_pedido, listar_pedidos, cancelar_pedido
from services.pacotes import PACOTES

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
            [InlineKeyboardButton(nome, callback_data=f"pacote:{categoria}:{nome}")]
            for nome in pacotes
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

        instrucoes = {
            "Seguidores Mundiais": "Envie agora o *@usuario* ou o *link do perfil do Instagram* que irá receber os seguidores.",
            "Seguidores Brasileiros": "Envie agora o *@usuario* ou o *link do perfil do Instagram* que irá receber os seguidores.",
            "Curtidas Instagram": "Envie agora o *link da publicação* que deve receber as curtidas.",
            "Visualizações Reels": "Envie agora o *link do Reels* que deve receber as visualizações.",
            "Visualizações Stories": "Envie agora o *link dos stories* que deve receber as visualizações.",
            "Comentários IA": "Envie agora o *link da publicação* que deseja receber os comentários gerados por IA."
        }

        instrucao = instrucoes.get(categoria, "Envie agora o link ou identificador necessário para o pacote escolhido.")
        await query.edit_message_text(
            f"Você escolheu o pacote *{nome_pacote}*\n\n{instrucao}\n\n"
            "Certifique-se de que o link está correto para evitar frustrações digitais!",
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

    # Validação básica
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
        f"💸 Pedido criado para *{titulo}*\n"
        f"Preço: R${preco:.2f}\n"
        f"🔗 Link: {entrada}\n\n"
        f"Clique abaixo para pagar:\n{link_pagamento}",
        parse_mode="Markdown"
    )

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
        "/start – Veja as opções iniciais\n"
        "/comprar – Comece seu pedido com botões interativos\n"
        "/status – Veja seus últimos pedidos e seus status\n"
        "/cancelar <id do pagamento> – Cancela um pedido que ainda não foi confirmado\n"
        "/ajuda – Você já está aqui, parabéns 👏\n"
        "/contato – Falar com o suporte do bot\n\n"
        "⚠️ Clique nos botões e siga as instruções. Evite usar a criatividade nos links."
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def contato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Para falar com o suporte, envie uma mensagem para [@Bielzeramartins](https://t.me/Bielzeramartins)",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

def register_user_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comprar", comprar))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("contato", contato))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CallbackQueryHandler(clique_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_link))
