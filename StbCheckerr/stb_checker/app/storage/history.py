import sqlite3
import os

class HistoryManager:
    def __init__(self, db_path="history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portal TEXT NOT NULL,
                    mac TEXT NOT NULL,
                    status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_entry(self, portal: str, mac: str, status: str):
        with sqlite3.connect(self.db_path) as conn:
            # Borrar entrada anterior duplicada si existe
            conn.execute('DELETE FROM history WHERE portal = ? AND mac = ?', (portal, mac))
            conn.execute('INSERT INTO history (portal, mac, status) VALUES (?, ?, ?)', (portal, mac, status))
            # Mantener un máximo de 50 registros
            conn.execute('''
                DELETE FROM history WHERE id NOT IN (
                    SELECT id FROM history ORDER BY timestamp DESC LIMIT 50
                )
            ''')
            conn.commit()

    def get_history(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT portal, mac, status FROM history ORDER BY timestamp DESC')
            return cursor.fetchall()
