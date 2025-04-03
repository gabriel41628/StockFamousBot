from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from services.pacotes_data import PACOTES
from services.pagamentos import criar_pagamento
from database.models import salvar_pedido, listar_pedidos, cancelar_pedido

pending_orders = {}  # Para armazenar o pacote escolhido temporariamente

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start – Mostra botão 'Ver Pacotes'."""
    keyboard = [[InlineKeyboardButton("🚀 Ver Pacotes", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Bem-vindo ao Bot!\nClique no botão abaixo para ver os pacotes!",
        reply_markup=reply_markup
    )

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Quando usuário clica em "Ver Pacotes" ou /comprar, mostra as categorias
    presentes no dicionário PACOTES (ex.: 'Seguidores Brasileiros', 'Curtidas BR', etc.).
    """
    keyboard = []
    for categoria in PACOTES.keys():
        keyboard.append([
            InlineKeyboardButton(f"📦 {categoria}", callback_data=f"categoria:{categoria}")
        ])

    await update.message.reply_text(
        "Escolha uma categoria:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def clique_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Toda vez que o usuário clica em um botão inline, cai aqui.
    Precisamos verificar qual o callback_data para agir.
    """
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat.id

    # Sempre é bom dar um answer() para confirmar que recebemos o callback
    await query.answer()

    # Se for "menu", chamamos a função 'comprar' para exibir as categorias
    if data == "menu":
        # Note: aqui usamos 'edit_message_text' ou 'send_message' dependendo do fluxo
        # Se quisermos substituir a mensagem anterior, usamos 'edit_message_text'.
        # Se quisermos mandar uma nova, podemos chamar "await comprar(update, context)" direto.
        await query.edit_message_text("Carregando categorias...")
        # Agora chama a função que monta o teclado de categorias.
        # Mas a 'comprar' envia 'update.message.reply_text', e aqui nós temos 'query.message'...
        # Uma forma simples é criar uma versão de 'comprar' que aceite "update, context" via callback.
        # Para simplificar, vamos mandar uma nova mensagem normal:
        
        categorias_keyboard = []
        for categoria in PACOTES.keys():
            categorias_keyboard.append([
                InlineKeyboardButton(f"📦 {categoria}", callback_data=f"categoria:{categoria}")
            ])
        await query.message.reply_text(
            "Escolha uma categoria:",
            reply_markup=InlineKeyboardMarkup(categorias_keyboard)
        )

    elif data.startswith("categoria:"):
        # data: "categoria:Seguidores Brasileiros"
        _, categoria = data.split(":", 1)
        pacotes = PACOTES.get(categoria, {})

        if not pacotes:
            await query.edit_message_text("❌ Nenhum pacote encontrado nessa categoria.")
            return

        # Monta teclado de pacotes
        keyboard = []
        for nome_pacote, info in pacotes.items():
            preco = info.get("preco", 0.0)
            text_btn = f"{nome_pacote} – R${preco:.2f}"
            callback = f"pacote:{categoria}:{nome_pacote}"
            keyboard.append([InlineKeyboardButton(text_btn, callback_data=callback)])

        # Botão de voltar
        keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="menu")])

        await query.edit_message_text(
            text=f"*{categoria}*\n\nEscolha um pacote:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("pacote:"):
        # data: "pacote:Seguidores Brasileiros:100 Seguidores 🇧🇷"
        _, categoria, nome_pacote = data.split(":", 2)
        pacote = PACOTES.get(categoria, {}).get(nome_pacote)

        if not pacote:
            await query.edit_message_text("❌ Pacote não encontrado.")
            return

        # Armazena info temporariamente
        pending_orders[chat_id] = {
            "categoria": categoria,
            "pacote": nome_pacote,
            "dados": pacote
        }

        await query.edit_message_text(
            f"Você escolheu o pacote *{nome_pacote}*\n\n"
            "Envie agora o link ou @usuario para continuar.",
            parse_mode="Markdown"
        )

async def receber_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Quando o usuário manda uma mensagem de texto que não é comando,
    verificamos se ele estava em 'pending_orders' para capturar o link/@.
    """
    chat_id = update.message.chat.id

    if chat_id not in pending_orders:
        # Não está escolhendo pacote nesse momento
        return

    link_ou_usuario = update.message.text.strip()
    pedido = pending_orders.pop(chat_id)  # remove do pending
    categoria = pedido["categoria"]
    pacote_nome = pedido["pacote"]
    dados = pedido["dados"]

    preco = dados["preco"]
    service_id = dados["id"]
    titulo = f"{pacote_nome}"

    if not (link_ou_usuario.startswith("@") or link_ou_usuario.startswith("http")):
        await update.message.reply_text("⚠️ Envie um link válido ou @usuário.")
        return

    # Cria o pagamento (se estiver usando Mercado Pago)
    link_pagamento, mp_id = criar_pagamento(titulo, preco)
    if not link_pagamento:
        await update.message.reply_text("❌ Erro ao gerar pagamento.")
        return

    # Salva pedido no banco
    salvar_pedido(
        chat_id=chat_id,
        servico=titulo,
        link=link_ou_usuario,
        preco=preco,
        mp_id=mp_id,
        service_id=service_id
    )

    await update.message.reply_text(
        f"💸 Pedido criado para *{titulo}*\n"
        f"Valor: R${preco:.2f}\n"
        f"🔗 Link de pagamento: {link_pagamento}",
        parse_mode="Markdown"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pedidos = listar_pedidos()
    chat_id = update.message.chat.id

    resposta = "📊 *Seus últimos pedidos:*\n\n"
    encontrados = False

    for p in pedidos:
        # p => (id, chat_id, servico, link, preco, status, mp_id, service_id)
        if p[1] == chat_id:
            encontrados = True
            resposta += (
                f"ID: {p[0]}\n"
                f"Pacote: {p[2]}\n"
                f"Link/Usuário: {p[3]}\n"
                f"Preço: R${p[4]:.2f}\n"
                f"Status: {p[5]}\n"
                f"MP ID: {p[6]}\n\n"
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
    await update.message.reply_text("Suporte: @SeuUserSuporte")

def register_user_handlers(app):
    """Registra todos os handlers necessários no 'app' (Application)."""
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comprar", comprar))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("contato", contato))
    # Trata callbacks inline de botões
    app.add_handler(CallbackQueryHandler(clique_callback))
    # Mensagens de texto que não sejam comandos:
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_link))
