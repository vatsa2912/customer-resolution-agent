from flask import request, jsonify
from app.api import api_bp
from app.services.action_service import ActionService
from app.database.repositories import ActionRepository

action_service = ActionService()
act_repo = ActionRepository()

@api_bp.post("/action/confirm")
def confirm_action():
    payload = request.get_json(silent=True) or {}
    action_id = payload.get("action_id")
    if not action_id:
        return jsonify({"error": "action_id is required"}), 400

    result = action_service.confirm_action(int(action_id))
    return jsonify(result)

@api_bp.post("/action/cancel")
def cancel_action():
    payload = request.get_json(silent=True) or {}
    action_id = payload.get("action_id")
    reason = payload.get("reason", "Cancelled by user")
    if not action_id:
        return jsonify({"error": "action_id is required"}), 400

    result = action_service.cancel_action(int(action_id), reason=reason)
    return jsonify(result)

@api_bp.get("/actions/<customer_key>")
def get_customer_actions(customer_key):
    actions = act_repo.get_by_customer(customer_key)
    return jsonify(actions)
