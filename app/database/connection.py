import sqlite3
from pathlib import Path
from typing import Optional
from app.config import Config

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or Config.DATABASE_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    conn = get_db_connection(db_path)
    try:
        with conn:
            # Check and migrate legacy tables if present
            table_info = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'").fetchone()
            if table_info:
                cols = [col[1] for col in conn.execute("PRAGMA table_info(messages)").fetchall()]
                if "conversation_id" not in cols:
                    conn.execute("DROP TABLE IF EXISTS messages")

            act_info = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='actions'").fetchone()
            if act_info:
                cols = [col[1] for col in conn.execute("PRAGMA table_info(actions)").fetchall()]
                if "idempotency_key" not in cols:
                    conn.execute("DROP TABLE IF EXISTS actions")

            conn.executescript("""
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    pnr TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    travel_history TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    pnr TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                );

                CREATE TABLE IF NOT EXISTS flights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flight_number TEXT NOT NULL,
                    booking_pnr TEXT NOT NULL,
                    route TEXT NOT NULL,
                    date TEXT NOT NULL,
                    scheduled_departure TEXT NOT NULL,
                    new_departure TEXT,
                    status TEXT NOT NULL,
                    reason TEXT,
                    delay_hours REAL DEFAULT 0,
                    is_return INTEGER DEFAULT 0,
                    FOREIGN KEY (booking_pnr) REFERENCES bookings(pnr)
                );

                CREATE TABLE IF NOT EXISTS policies (
                    code TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    rule_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_key TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    customer_key TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS agent_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    customer_key TEXT NOT NULL,
                    primary_intent TEXT,
                    secondary_intents TEXT,
                    policy_codes TEXT,
                    decision TEXT,
                    reason TEXT,
                    proposed_action TEXT,
                    requires_confirmation INTEGER DEFAULT 0,
                    requires_escalation INTEGER DEFAULT 0,
                    provider_used TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    customer_key TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT NOT NULL,
                    idempotency_key TEXT UNIQUE,
                    created_at TEXT NOT NULL,
                    executed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS escalations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    customer_key TEXT NOT NULL,
                    category TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    details TEXT NOT NULL,
                    supervisor_notes TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_customer ON messages(customer_key);
                CREATE INDEX IF NOT EXISTS idx_actions_customer ON actions(customer_key);
                CREATE INDEX IF NOT EXISTS idx_escalations_customer ON escalations(customer_key);
                CREATE INDEX IF NOT EXISTS idx_flights_pnr ON flights(booking_pnr);
            """)
    finally:
        conn.close()
