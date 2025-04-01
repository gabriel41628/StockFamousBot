from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from services import pagamentos, upmidias
from database.models import salvar_pedido, criar_db

USERS_PEDINDO = {}

def register_user_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processa_mensagem))
    criar_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [["Seguidores BR", "Curtidas Instagram", "Visualizações"]]
    reply_markup = ReplyKeyboardMarkup(teclado, one_time_keyboard=True)
    await update.message.reply_text("🚀 Olá! Escolha um serviço para começar:", reply_markup=reply_markup)

async def processa_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    user_id = update.message.chat_id

    precos = {
        "Seguidores BR": ("Seguidores brasileiros", 12.0, 101),
        "Curtidas Instagram": ("Curtidas em post", 9.0, 102),
        "Visualizações": ("Visualizações em Reels", 7.0, 103)
    }

    if texto in precos:
        USERS_PEDINDO[user_id] = precos[texto]
        await update.message.reply_text("🧾 Agora envie o link ou @ do perfil/post:")
    elif user_id in USERS_PEDINDO:
        nome_servico, valor, id_servico = USERS_PEDINDO[user_id]
        link_perfil = texto
        url_pagamento, pagamento_id = pagamentos.criar_pagamento(nome_servico, valor)

        salvar_pedido(user_id, nome_servico, link_perfil, valor, "aguardando", pagamento_id, id_servico)
        await update.message.reply_text(f"✅ Pague no link abaixo para prosseguir:\n{url_pagamento}")
        del USERS_PEDINDO[user_id]
    else:
        await update.message.reply_text("🤔 Comando não reconhecido. Use /start.")

