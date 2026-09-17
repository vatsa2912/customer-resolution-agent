from flask import jsonify
from app.api import api_bp
from app.policies.policy_data import POLICIES_MASTER
from app.ai.provider_factory import ProviderFactory
from app.database.repositories import AuditRepository

audit_repo = AuditRepository()

@api_bp.get("/policies")
def get_policies():
    return jsonify(list(POLICIES_MASTER.values()))

@api_bp.get("/system/status")
def system_status():
    provider = ProviderFactory.get_provider()
    health = provider.health_check()
    return jsonify({
        "status": "operational",
        "provider": health.get("provider"),
        "model": health.get("model"),
        "provider_status": health.get("status"),
        "message": health.get("message"),
        "exercise_date": "Wednesday, 23 September 2026",
        "recent_audit": audit_repo.get_recent(limit=5)
    })
