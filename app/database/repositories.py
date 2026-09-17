import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.database.connection import get_db_connection

class CustomerRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_by_key(self, customer_key: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_key,)).fetchone()
            if not row:
                return None
            cust = dict(row)
            
            # Fetch flights
            flight_rows = conn.execute(
                "SELECT * FROM flights WHERE booking_pnr = ? ORDER BY id",
                (cust["pnr"],)
            ).fetchall()
            cust["flights"] = [dict(f) for f in flight_rows]
            return cust
        finally:
            conn.close()

    def get_all(self) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM customers").fetchall()
            result = []
            for r in rows:
                cust = dict(r)
                f_rows = conn.execute("SELECT * FROM flights WHERE booking_pnr = ?", (cust["pnr"],)).fetchall()
                cust["flights"] = [dict(f) for f in f_rows]
                result.append(cust)
            return result
        finally:
            conn.close()

class PolicyRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_all(self) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM policies").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                try:
                    d["rules"] = json.loads(d["rule_json"])
                except Exception:
                    d["rules"] = {}
                result.append(d)
            return result
        finally:
            conn.close()

    def get_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            row = conn.execute("SELECT * FROM policies WHERE code = ?", (code,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["rules"] = json.loads(d["rule_json"])
            return d
        finally:
            conn.close()

class ConversationRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_or_create_active(self, customer_key: str) -> int:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                row = conn.execute(
                    "SELECT id FROM conversations WHERE customer_key = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
                    (customer_key,)
                ).fetchone()
                if row:
                    return row["id"]
                now = datetime.now().isoformat(timespec="seconds")
                cursor = conn.execute(
                    "INSERT INTO conversations (customer_key, status, created_at, updated_at) VALUES (?, 'active', ?, ?)",
                    (customer_key, now, now)
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def add_message(self, conversation_id: int, customer_key: str, sender: str, content: str, intent: Optional[str] = None, metadata: Optional[Dict] = None):
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                now = datetime.now().isoformat(timespec="seconds")
                meta_str = json.dumps(metadata) if metadata else None
                conn.execute(
                    """INSERT INTO messages (conversation_id, customer_key, sender, content, intent, metadata, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (conversation_id, customer_key, sender, content, intent, meta_str, now)
                )
                conn.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now, conversation_id)
                )
        finally:
            conn.close()

    def get_messages(self, customer_key: str, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM messages WHERE customer_key = ? ORDER BY id ASC LIMIT ?",
                (customer_key, limit)
            ).fetchall()
            messages = []
            for r in rows:
                d = dict(r)
                if d.get("metadata"):
                    try:
                        d["metadata"] = json.loads(d["metadata"])
                    except Exception:
                        pass
                messages.append(d)
            return messages
        finally:
            conn.close()

    def clear_history(self, customer_key: str):
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute("DELETE FROM messages WHERE customer_key = ?", (customer_key,))
                conn.execute("DELETE FROM actions WHERE customer_key = ?", (customer_key,))
                conn.execute("DELETE FROM escalations WHERE customer_key = ?", (customer_key,))
                conn.execute("DELETE FROM agent_decisions WHERE customer_key = ?", (customer_key,))
                conn.execute("DELETE FROM conversations WHERE customer_key = ?", (customer_key,))
        finally:
            conn.close()

class ActionRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def create(self, customer_key: str, action_type: str, status: str, details: str, idempotency_key: Optional[str] = None, conversation_id: Optional[int] = None) -> int:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                now = datetime.now().isoformat(timespec="seconds")
                executed_at = now if status in ("executed", "approved") else None
                cursor = conn.execute(
                    """INSERT INTO actions (conversation_id, customer_key, action_type, status, details, idempotency_key, created_at, executed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (conversation_id, customer_key, action_type, status, details, idempotency_key, now, executed_at)
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def get_by_id(self, action_id: int) -> Optional[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            row = conn.execute("SELECT * FROM actions WHERE id = ?", (action_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_by_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            row = conn.execute("SELECT * FROM actions WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_status(self, action_id: int, status: str, details: Optional[str] = None) -> bool:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                now = datetime.now().isoformat(timespec="seconds")
                executed_at = now if status in ("executed", "approved") else None
                if details:
                    conn.execute(
                        "UPDATE actions SET status = ?, details = ?, executed_at = ? WHERE id = ?",
                        (status, details, executed_at, action_id)
                    )
                else:
                    conn.execute(
                        "UPDATE actions SET status = ?, executed_at = ? WHERE id = ?",
                        (status, executed_at, action_id)
                    )
                return True
        finally:
            conn.close()

    def get_latest_pending(self, customer_key: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM actions WHERE customer_key = ? AND status = 'awaiting_confirmation' ORDER BY id DESC LIMIT 1",
                (customer_key,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_by_customer(self, customer_key: str) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM actions WHERE customer_key = ? ORDER BY id DESC",
                (customer_key,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

class EscalationRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def create(self, customer_key: str, category: str, reason: str, details: str, conversation_id: Optional[int] = None) -> int:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                now = datetime.now().isoformat(timespec="seconds")
                cursor = conn.execute(
                    """INSERT INTO escalations (conversation_id, customer_key, category, reason, status, details, created_at)
                       VALUES (?, ?, ?, ?, 'pending', ?, ?)""",
                    (conversation_id, customer_key, category, reason, details, now)
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def get_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM escalations ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_by_customer(self, customer_key: str) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM escalations WHERE customer_key = ? ORDER BY id DESC", (customer_key,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

class AuditRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def log(self, event_type: str, actor: str, details: str):
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                now = datetime.now().isoformat(timespec="seconds")
                conn.execute(
                    "INSERT INTO audit_logs (event_type, actor, details, created_at) VALUES (?, ?, ?, ?)",
                    (event_type, actor, details, now)
                )
        finally:
            conn.close()

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
