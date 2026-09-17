"""
Backward compatibility wrapper for database operations.
Delegates to app.database.
"""
from app.database.connection import get_db_connection, init_db
from app.database.repositories import ConversationRepository, ActionRepository

_conv = ConversationRepository()
_act = ActionRepository()

def save_message(customer_key, sender, message):
    conv_id = _conv.get_or_create_active(customer_key)
    _conv.add_message(conv_id, customer_key, sender, message)

def save_action(customer_key, action):
    conv_id = _conv.get_or_create_active(customer_key)
    _act.create(
        customer_key=customer_key,
        action_type=action.get("type") or action.get("action_type", "unknown"),
        status=action.get("status", "executed"),
        details=action.get("details", ""),
        conversation_id=conv_id
    )

def get_conversation(customer_key):
    return {
        "messages": _conv.get_messages(customer_key),
        "actions": _act.get_by_customer(customer_key)
    }

__all__ = ["init_db", "save_message", "save_action", "get_conversation", "get_db_connection"]
