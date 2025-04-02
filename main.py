from handlers import setup_handlers
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
import logging
import asyncio

logging.basicConfig(level=logging.INFO)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    setup_handlers(app)
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    from telegram.ext import ApplicationBuilder
    from config import BOT_TOKEN
    from handlers import setup_handlers

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    setup_handlers(app)
    app.run_polling()
