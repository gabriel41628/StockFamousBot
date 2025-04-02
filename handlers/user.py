from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from services.pagamentos import criar_pagamento
from database.models import salvar_pedido, listar_pedidos, cancelar_pedido
from services.pacotes import PACOTES

# Envia mensagem de boas-vindas
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "👋 Bem-vindo ao *Stock Famous Bot*!\n\n"
        "Compre seguidores, curtidas, visualizações e comentários com poucos cliques.\n\n"
        "Use o comando /comprar para iniciar uma compra.\n"
        "Use /pacotes para visualizar todos os serviços disponíveis.\n"
        "Use /ajuda para mais informações."
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

# Mostra categorias principais
async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"📦 {categoria}", callback_data=f"categoria:{categoria}")]
        for categoria in PACOTES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha uma categoria:", reply_markup=reply_markup)

# Trata cliques nos botões
async def clique_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("categoria:"):
        categoria = data.split(":", 1)[1]
        pacotes = PACOTES.get(categoria, {})

        keyboard = [
            [InlineKeyboardButton(nome, callback_data=f"pacote:{nome}")]
            for nome in pacotes
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="voltar")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"{categoria} selecionado. Escolha um pacote:", reply_markup=reply_markup)

    elif data.startswith("pacote:"):
        nome_pacote = data.split(":", 1)[1]
        for categoria in PACOTES.values():
            if nome_pacote in categoria:
                context.user_data["pacote"] = {
                    "nome": nome_pacote,
                    "dados": categoria[nome_pacote]
                }
                break

        pacote = context.user_data.get("pacote")
        preco = pacote["dados"]["preco"]
        await query.edit_message_text(
            f"Você escolheu o pacote *{nome_pacote}*\n"
            "\n"
            "Envie agora o link ou identificador necessário para o pacote escolhido.\n"
            "\n"
            "Certifique-se de que o link está correto para evitar frustrações digitais!\n"
            f"\n💸 Valor: *R${preco:.2f}*",
            parse_mode="Markdown"
        )

    elif data == "voltar":
        await comprar(update, context)

# Recebe o link enviado após a escolha do pacote
async def receber_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pacote = context.user_data.get("pacote")
    if not pacote:
        return

    link = update.message.text.strip()

    if not link.startswith("http") and not link.startswith("@"):
        await update.message.reply_text("⚠️ Opa! Isso não parece um link válido.\nTenta de novo com um link começando com http ou com @ para nome de usuário.")
        return

    dados = pacote["dados"]
    titulo = pacote["nome"]
    preco = dados["preco"]
    service_id = dados.get("id_seguidores") or dados.get("id")
    quantidade = dados.get("quantidade", 100)
    chat_id = update.message.chat_id

    link_pagamento, mp_id = criar_pagamento(titulo, preco)

    if not link_pagamento:
        await update.message.reply_text("❌ Erro ao gerar pagamento. Tente novamente mais tarde.")
        return

    salvar_pedido(service_id, chat_id, link, mp_id, status="aguardando", quantidade=quantidade)

    await update.message.reply_text(
        f"✅ Pedido criado com sucesso!\n"
        f"Produto: *{titulo}*\n"
        f"Valor: R${preco:.2f}\n"
        f"\n👉 Clique abaixo para pagar:\n{link_pagamento}",
        parse_mode="Markdown"
    )
    context.user_data.pop("pacote", None)

# Lista todos os pacotes (modo texto)
async def listar_pacotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "📦 *Pacotes disponíveis:*\n\n"
\n"
    for categoria, pacotes in PACOTES.items():
        texto += f"*{categoria}:*\n"
        for nome, dados in pacotes.items():
            preco = dados["preco"]
            descricao = dados.get("descricao", "")
            texto += f"• *{nome}* — R${preco:.2f}\n_{descricao}_\n"
        texto += "\n"

    await update.message.reply_text(texto, parse_mode="Markdown")

# Status dos pedidos
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

# Cancelar pedido
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Use assim: /cancelar <ID do pagamento>")
        return

    mp_id = context.args[0]
    chat_id = update.message.chat_id
    cancelar_pedido(mp_id, chat_id)

    await update.message.reply_text("❌ Pedido cancelado com sucesso (ou ele já estava cancelado mesmo).")

# Ajuda
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📌 *Como usar o Stock Famous Bot:*\n\n"
        "/start – Mostra mensagem de boas-vindas e instruções\n"
        "/comprar – Inicia o processo de compra por botões\n"
        "/pacotes – Lista todos os pacotes com valores e descrições\n"
        "/status – Veja o status dos seus últimos pedidos\n"
        "/cancelar <id> – Cancela um pedido\n"
        "/ajuda – Exibe este menu de ajuda\n"
        "/contato – Suporte via Telegram\n"
        "/cafe – Um carinho digital em forma de comando ☕"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

# Cafe
async def cafe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("☕ Café saindo! Não resolve bugs, mas acalma a alma.")

# Contato
async def contato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Para suporte, fale com [@Bielzeramartins](https://t.me/Bielzeramartins)",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

def register_user_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comprar", comprar))
    app.add_handler(CommandHandler("pacotes", listar_pacotes))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("cafe", cafe))
    app.add_handler(CommandHandler("contato", contato))
    app.add_handler(CallbackQueryHandler(clique_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_link))
