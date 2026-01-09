import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='desafios.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Tabela de desafios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS desafios (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            username TEXT,
            ign TEXT,
            initial_class TEXT,
            current_class TEXT,
            rerolls_used INTEGER DEFAULT 0,
            accepted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')
        
        # Tabela de logs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            desafio_id TEXT,
            usuario TEXT,
            mensagem TEXT,
            timestamp TIMESTAMP
        )
        ''')
        
        self.conn.commit()
    
    def create_challenge(self, **kwargs):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO desafios 
        (id, user_id, username, ign, initial_class, current_class, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            kwargs['challenge_id'],
            kwargs['user_id'],
            kwargs['username'],
            kwargs['ign'],
            kwargs['initial_class'],
            kwargs['current_class'],
            now,
            now
        ))
        
        self.conn.commit()
    
    def get_active_challenge(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM desafios 
        WHERE user_id = ? AND accepted = FALSE
        ORDER BY created_at DESC LIMIT 1
        ''', (user_id,))
        
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        
        return dict(zip(columns, row)) if row else None
    
    def has_active_challenge(self, user_id):
        return self.get_active_challenge(user_id) is not None
    
    def update_challenge(self, challenge_id, **kwargs):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [now, challenge_id]
        
        cursor.execute(f'''
        UPDATE desafios 
        SET {set_clause}, updated_at = ?
        WHERE id = ?
        ''', values)
        
        self.conn.commit()
    
    def accept_challenge(self, challenge_id):
        self.update_challenge(challenge_id, accepted=True)
    
    def get_all_active_challenges(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM desafios WHERE accepted = FALSE')
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]