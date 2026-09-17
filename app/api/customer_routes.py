from flask import jsonify
from app.api import api_bp
from app.database.repositories import CustomerRepository, ConversationRepository, ActionRepository, EscalationRepository

cust_repo = CustomerRepository()
conv_repo = ConversationRepository()
act_repo = ActionRepository()
esc_repo = EscalationRepository()

@api_bp.get("/customers")
def get_customers():
    return jsonify(cust_repo.get_all())

@api_bp.get("/customer/<customer_key>")
def get_customer(customer_key):
    cust = cust_repo.get_by_key(customer_key)
    if not cust:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(cust)

@api_bp.get("/conversation/<customer_key>")
def get_conversation(customer_key):
    messages = conv_repo.get_messages(customer_key)
    actions = act_repo.get_by_customer(customer_key)
    escalations = esc_repo.get_by_customer(customer_key)
    pending_action = act_repo.get_latest_pending(customer_key)

    return jsonify({
        "customer_key": customer_key,
        "messages": messages,
        "actions": actions,
        "escalations": escalations,
        "pending_action": pending_action
    })

@api_bp.post("/conversation/<customer_key>/clear")
def clear_conversation(customer_key):
    conv_repo.clear_history(customer_key)
    return jsonify({"success": True, "message": f"Session cleared for {customer_key}"})
