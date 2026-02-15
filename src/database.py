"""
SQLite session store with WAL mode for concurrent access.
"""

import json
import sqlite3
import threading
from typing import Optional, Dict
from src.config import DATABASE_PATH

_local = threading.local()


def get_connection(db_path: str) -> sqlite3.Connection:
    if not hasattr(_local, 'conn') or _local.conn is None:
        conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        conn.execute('PRAGMA cache_size=10000;')
        conn.execute('PRAGMA temp_store=memory;')
        conn.row_factory = sqlite3.Row
        _local.conn = conn
    return _local.conn


class SessionManager:

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON sessions(session_id)')
        conn.commit()
        conn.close()

    def get_session(self, session_id: str) -> Optional[Dict]:
        for attempt in range(3):
            try:
                conn = get_connection(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT state_json FROM sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                return json.loads(row[0]) if row else None
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < 2:
                    import time
                    time.sleep(0.05 * (attempt + 1))
                    continue
                return None

    def save_session(self, session_id: str, state: Dict):
        for attempt in range(3):
            try:
                conn = get_connection(self.db_path)
                state_json = json.dumps(state, default=str)
                conn.execute('''
                    INSERT INTO sessions (session_id, state_json, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(session_id)
                    DO UPDATE SET state_json = excluded.state_json, updated_at = CURRENT_TIMESTAMP
                ''', (session_id, state_json))
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < 2:
                    import time
                    time.sleep(0.05 * (attempt + 1))
                    continue
                return

    def delete_session(self, session_id: str):
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
        except Exception:
            pass
