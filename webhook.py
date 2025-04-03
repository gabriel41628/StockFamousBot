import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from config import BOT_TOKEN, WEBHOOK_URL
from handlers import start, handle_message

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização do Flask
app = Flask(__name__)

# Inicialização do bot e dispatcher
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)

# Definição dos handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    """Endpoint que recebe as atualizações do Telegram."""
    update = Update.de_json(request.get_json(), bot)
    dispatcher.process_update(update)
    return 'OK'

def set_webhook():
    """Configura o webhook no Telegram."""
    s = bot.setWebhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
    if s:
        logger.info(f"Webhook configurado com sucesso em {WEBHOOK_URL}/{BOT_TOKEN}")
    else:
        logger.error("Falha ao configurar o webhook.")

if __name__ == '__main__':
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
