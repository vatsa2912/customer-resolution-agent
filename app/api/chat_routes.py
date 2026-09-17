from flask import request, jsonify
from app.api import api_bp
from app.agents.resolution_agent import CustomerResolutionAgent

agent = CustomerResolutionAgent()

@api_bp.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    customer_key = payload.get("customer_key") or ""
    force_provider = payload.get("force_provider")

    if not customer_key:
        return jsonify({"error": "Please select a customer (Priya, Arvind, or Meher)."}), 400

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    result = agent.handle(message, customer_key, force_provider=force_provider)
    return jsonify(result)
