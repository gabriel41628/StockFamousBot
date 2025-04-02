import sqlite3

def criar_db():
    conn = sqlite3.connect("dados.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario INTEGER,
            servico TEXT,
            link TEXT,
            preco REAL,
            status TEXT,
            mp_id TEXT,
            fornecedor_id TEXT,
            service_id INTEGER,
            chat_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def salvar_pedido(service_id, chat_id, link, mp_id, status="aguardando", quantidade=100):
    conn = sqlite3.connect("dados.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO pedidos (service_id, chat_id, link, mp_id, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (service_id, chat_id, link, mp_id, status))
    conn.commit()
    conn.close()

def salvar_pedido_completo(usuario, servico, link, preco, status, mp_id, service_id):
    conn = sqlite3.connect("dados.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO pedidos (usuario, servico, link, preco, status, mp_id, service_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (usuario, servico, link, preco, status, mp_id, service_id))
    conn.commit()
    conn.close()

def atualizar_status(mp_id, status, fornecedor_id):
    conn = sqlite3.connect("dados.db")
    c = conn.cursor()
    c.execute('''
        UPDATE pedidos
        SET status = ?, fornecedor_id = ?
        WHERE mp_id = ?
    ''', (status, fornecedor_id, mp_id))
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
