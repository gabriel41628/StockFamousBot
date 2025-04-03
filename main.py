from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from handlers.user import register_user_handlers
import logging

# IMPORTANTE: vamos chamar criar_db() antes de subir o bot
from database.models import criar_db

logging.basicConfig(level=logging.INFO)

def main():
    # Cria (se não existir) o banco de dados e tabela 'pedidos'
    criar_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_user_handlers(app)

    logging.info("Bot iniciado. Aguardando mensagens...")
    app.run_polling()

if __name__ == "__main__":
    main()
