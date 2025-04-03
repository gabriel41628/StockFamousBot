import sqlite3

def criar_db():
    conn = sqlite3.connect("dados.db")
    c = conn.cursor()

    # Vamos criar tabela com colunas coerentes:
    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            servico TEXT,
            link TEXT,
            preco REAL,
            status TEXT,
            mp_id TEXT,
            service_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def salvar_pedido(chat_id, servico, link, preco, mp_id, status="aguardando", service_id=None):
    conn = sqlite3.connect("dados.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO pedidos (chat_id, servico, link, preco, status, mp_id, service_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (chat_id, servico, link, preco, status, mp_id, service_id))
    conn.commit()
    conn.close()

def cancelar_pedido(mp_id, chat_id):
    conn = sqlite3.connect("dados.db")
    c = conn.cursor()
    c.execute('''
        UPDATE pedidos
        SET status = 'cancelado'
        WHERE mp_id = ? AND chat_id = ? AND status = 'aguardando'
    ''', (mp_id, chat_id))
    conn.commit()
    conn.close()

def listar_pedidos():
    conn = sqlite3.connect("dados.db")
    c = conn.cursor()
    c.execute('SELECT * FROM pedidos ORDER BY id DESC LIMIT 10')
    rows = c.fetchall()
    conn.close()
    return rows
