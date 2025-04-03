from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from handlers.user import register_user_handlers
from database.models import criar_db
import logging

logging.basicConfig(level=logging.INFO)

def main():
    criar_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_user_handlers(app)
    app.run_polling()

if __name__ == "__main__":
    main()
