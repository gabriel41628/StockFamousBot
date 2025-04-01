# Stock Famous Bot

Bot de Telegram para revenda automatizada de serviços SMM (seguidores, curtidas, views) usando a API da UpMídias e integração com Mercado Pago.

## 🚀 Funcionalidades

- Catálogo de serviços com botões
- Geração de link dinâmico de pagamento via Mercado Pago
- Confirmação automática por webhook
- Envio automático de pedido para API SMM
- Comando de admin: `/pedidos`
- Banco de dados local (SQLite)

---

## 📦 Estrutura

- `main.py`: inicia o bot
- `webhook.py`: servidor Flask para notificação de pagamento
- `handlers/`: comandos do usuário e admin
- `services/`: integração com APIs externas
- `database/`: funções do SQLite
- `config.py` + `.env`: credenciais
- `assets/`: imagens e logo

---

## ⚙️ Como rodar localmente

1. Instale as dependências:
```bash
pip install -r requirements.txt
