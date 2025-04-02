from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from handlers import setup_handlers
import logging

logging.basicConfig(level=logging.INFO)

app = ApplicationBuilder().token(BOT_TOKEN).build()
setup_handlers(app)

app.run_polling()
