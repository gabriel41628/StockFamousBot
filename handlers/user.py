from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from services.pagamentos import criar_pagamento
from database.models import salvar_pedido, listar_pedidos, cancelar_pedido
from services.pacotes_data import PACOTES

pending_orders = {}  # dicionário para armazenar pacote temporariamente

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚀 Ver Pacotes", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Bem-vindo ao *Stock Famous Bot*!\nClique abaixo para ver os pacotes!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Lista as categorias do dicionário PACOTES:
    keyboard = [[InlineKeyboardButton(f"📦 {categoria}", callback_data=f"categoria:{categoria}")] 
                for categoria in PACOTES]
    await update.message.reply_text("Escolha uma categoria:", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def clique_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat.id

    if data.startswith("categoria:"):
        categoria = data.split(":", 1)[1]
        pacotes = PACOTES.get(categoria, {})
        keyboard = []
        for nome, p in pacotes.items():
            preco_str = f"R${p['preco']:.2f}"
            keyboard.append([InlineKeyboardButton(f"{nome} – {preco_str}", 
                                                  callback_data=f"pacote:{categoria}:{nome}")])
        keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="menu")])
        await query.edit_message_text(
            f"*{categoria}*\n\nEscolha um pacote:", 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="Markdown"
        )

    elif data.startswith("pacote:"):
        # data = "pacote:categoria:nome"
        _, categoria, nome_pacote = data.split(":", 2)
        pacote = PACOTES.get(categoria, {}).get(nome_pacote)
        if not pacote:
            await query.edit_message_text("❌ Pacote não encontrado.")
            return
        # Armazena info no pending_orders para sabermos qual pacote o user escolheu
        pending_orders[chat_id] = {
            "categoria": categoria,
            "pacote": nome_pacote,
            "dados": pacote
        }
        await query.edit_message_text(
            f"Você escolheu o pacote *{nome_pacote}*\n\n"
            "Agora, envie o link (http...) ou @usuario para continuarmos.",
            parse_mode="Markdown"
        )

    elif data == "menu":
        # Volta pro menu principal de escolha de categoria
        await comprar(update, context)

async def receber_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    # Verifica se o user estava escolhendo algum pacote
    if chat_id not in pending_orders:
        return

    entrada = update.message.text.strip()
    pedido = pending_orders.pop(chat_id)  # remove das pendências
    categoria = pedido["categoria"]
    pacote_nome = pedido["pacote"]
    pacote = pedido["dados"]

    preco = pacote["preco"]
    service_id = pacote["id"]  # definimos que tudo é "id" no dicionário
    titulo = f"{pacote_nome}"  # ex: "100 Seguidores"

    if not (entrada.startswith("@") or entrada.startswith("http")):
        await update.message.reply_text("⚠️ Por favor, envie um link ou @usuário válido.")
        return

    # Cria pagamento no Mercado Pago
    link_pagamento, mp_id = criar_pagamento(titulo, preco)
    if not link_pagamento:
        await update.message.reply_text("❌ Erro ao gerar pagamento no Mercado Pago.")
        return

    # Salva no banco
    salvar_pedido(
        chat_id=chat_id,
        servico=titulo,
        link=entrada,
        preco=preco,
        mp_id=mp_id,
        status="aguardando",
        service_id=service_id
    )

    await update.message.reply_text(
        f"💸 *Pedido criado!* \n"
        f"Pacote: *{titulo}*\n"
        f"Valor: R${preco:.2f}\n"
        f"🔗 Link de pagamento: {link_pagamento}\n\n"
        "Após pagar, aguarde o status ser atualizado.",
        parse_mode="Markdown"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pedidos = listar_pedidos()
    chat_id = update.message.chat.id

    resposta = "📊 *Seus últimos pedidos:*\n\n"
    encontrados = False

    for p in pedidos:
        # p é uma tupla (id, chat_id, servico, link, preco, status, mp_id, service_id)
        # Indices:         0        1         2     3     4      5      6       7
        if p[1] == chat_id:
            encontrados = True
            pedido_id = p[0]
            servico = p[2]
            link = p[3]
            preco = p[4]
            status_ = p[5]
            mp_id = p[6]
            resposta += (
                f"**ID:** {pedido_id}\n"
                f"**Pacote:** {servico}\n"
                f"**Link/Usuário:** {link}\n"
                f"**Preço:** R${preco:.2f}\n"
                f"**Status:** `{status_}`\n"
                f"**MP_ID:** {mp_id}\n"
                "-------------------\n"
            )

    if not encontrados:
        resposta = "Você ainda não tem pedidos registrados."
    await update.message.reply_text(resposta, parse_mode="Markdown")

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use assim: /cancelar <mp_id>")
        return
    mp_id = context.args[0]
    cancelar_pedido(mp_id, update.message.chat.id)
    await update.message.reply_text("✅ Pedido cancelado (ou já estava cancelado).")

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandos disponíveis:\n"
        "/start - Iniciar\n"
        "/comprar - Comprar pacotes\n"
        "/status - Ver status dos pedidos\n"
        "/cancelar <mp_id> - Cancelar pedido\n"
        "/ajuda - Exibe este help\n"
        "/contato - Falar com o suporte\n"
    )

async def contato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Suporte: @SeuUserSuporte", parse_mode="Markdown")

def register_user_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comprar", comprar))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("contato", contato))
    app.add_handler(CallbackQueryHandler(clique_callback))
    # Filtro para texto "qualquer" (desde que não seja comando)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_link))
