from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database.models import listar_pedidos

def register_admin_handlers(app):
    app.add_handler(CommandHandler("pedidos", listar))

async def listar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != "836934282:
        await update.message.reply_text("🚫 Acesso negado.")
        return

    pedidos = listar_pedidos()
    resposta = "📦 Pedidos:\n\n" + "\n".join([f"{p[0]} - {p[1]} - {p[4]}" for p in pedidos])
    await update.message.reply_text(resposta or "Nenhum pedido.")
