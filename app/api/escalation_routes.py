from flask import jsonify
from app.api import api_bp
from app.services.escalation_service import EscalationService

esc_service = EscalationService()

@api_bp.get("/escalations")
def get_escalations():
    return jsonify(esc_service.get_all())
