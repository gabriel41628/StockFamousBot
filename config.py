import os

# Se você for usar variáveis de ambiente do Railway, set BOT_TOKEN e MERCADO_PAGO_TOKEN nelas.
# Caso contrário, coloque aqui fixo (NÃO recomendado em produção).

BOT_TOKEN = os.getenv("BOT_TOKEN", "SUA_TELEGRAM_BOT_TOKEN")
MERCADO_PAGO_TOKEN = os.getenv("MERCADO_PAGO_TOKEN", "SUA_MERCADO_PAGO_ACCESS_TOKEN")
