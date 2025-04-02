from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from services.pagamentos import criar_pagamento
from database.models import salvar_pedido, listar_pedidos, cancelar_pedido
from services.pacotes import PACOTES

# Armazena a etapa do fluxo do usuário
user_flow = {}

# Comando /start com explicação inicial
def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "👋 Bem-vindo ao *Stock Famous Bot*!
        
"
        "Aqui você pode comprar seguidores, curtidas, visualizações e muito mais.

"
        "Use os botões abaixo ou envie /comprar para começar."
    )
    return update.message.reply_text(texto, parse_mode="Markdown")

# Primeiro nível: mostra categorias
async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for categoria in PACOTES:
        keyboard.append([InlineKeyboardButton(f"📦 {categoria}", callback_data=f"categoria:{categoria}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha uma categoria de serviço:", reply_markup=reply_markup)

# Callback para categoria e pacotes
async def clique_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # Clique em uma categoria
    if data.startswith("categoria:"):
        categoria = data.split(":", 1)[1]
        pacotes = PACOTES.get(categoria, {})

        if not pacotes:
            await query.edit_message_text("❌ Nenhum pacote disponível nesta categoria.")
            return

        keyboard = []
        for nome in pacotes:
            keyboard.append([InlineKeyboardButton(nome, callback_data=f"comprar:{nome}")])

        keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="voltar")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"📦 *{categoria}* — escolha o pacote:", parse_mode="Markdown", reply_markup=reply_markup)
        return

    # Botão de voltar
    if data == "voltar":
        await comprar(query, context)
        return

    # Clique em um pacote
    if data.startswith("comprar:"):
        nome_pacote = data.split(":", 1)[1]
        pacote = None
        for categoria in PACOTES.values():
            if nome_pacote in categoria:
                pacote = categoria[nome_pacote]
                break

        if not pacote:
            await query.edit_message_text("🚫 Pacote não encontrado.")
            return

        chat_id = query.message.chat_id
        context.user_data['pacote_selecionado'] = (nome_pacote, pacote)
        user_flow[chat_id] = "esperando_link"

        await query.edit_message_text("🔗 Envie o link do perfil ou postagem para aplicar o serviço:")

# Recebe o link e finaliza o pedido
async def receber_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    etapa = user_flow.get(chat_id)

    if etapa != "esperando_link":
        return

    nome_pacote, pacote = context.user_data.get("pacote_selecionado", (None, None))
    link = update.message.text
    preco = pacote["preco"]
    service_id = pacote.get("id_seguidores") or pacote.get("id")
    quantidade = pacote.get("quantidade", 100)

    link_pagamento, mp_id = criar_pagamento(nome_pacote, preco)
    if not link_pagamento:
        await update.message.reply_text("❌ Erro ao gerar pagamento. Tente novamente mais tarde.")
        return

    salvar_pedido(service_id, chat_id, link, mp_id, status="aguardando", quantidade=quantidade)

    await update.message.reply_text(
        f"💸 Pedido criado para *{nome_pacote}*\n"
        f"Preço: R${preco:.2f}\n"
        f"🔗 Link: {link}\n\n"
        f"Clique abaixo para pagar:
{link_pagamento}",
        parse_mode="Markdown"
    )

    user_flow.pop(chat_id, None)

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
        "/comprar – Escolha uma categoria e selecione seu pacote\n"
        "/status – Veja seus últimos pedidos\n"
        "/cancelar <id do pagamento> – Cancele um pedido ainda não confirmado\n"
        "/pacotes – Veja todos os pacotes em formato de lista\n"
        "/ajuda – Você já está aqui, respira\n"
        "/cafe – Um agrado emocional\n"
        "/contato – Suporte diretamente comigo\n\n"
        "⚠️ Use os botões abaixo das mensagens para navegar."
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def cafe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("☕ Você recebeu um café virtual. Melhor que bugar no meio do pedido.")

async def contato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Para falar com o suporte, envie uma mensagem para [@Bielzeramartins](https://t.me/Bielzeramartins)",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_link))
