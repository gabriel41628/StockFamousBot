from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from handlers.user import register_user_handlers
import logging

logging.basicConfig(level=logging.INFO)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_user_handlers(app)
    app.run_polling()

if __name__ == "__main__":
    main()
