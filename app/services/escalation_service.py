from typing import Dict, Any, List, Optional
from app.database.repositories import EscalationRepository, AuditRepository

class EscalationService:
    def __init__(self, escalation_repo: Optional[EscalationRepository] = None):
        self.repo = escalation_repo or EscalationRepository()
        self.audit = AuditRepository()

    def create_escalation(
        self,
        customer_key: str,
        category: str,
        reason: str,
        details: str,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        esc_id = self.repo.create(
            customer_key=customer_key,
            category=category,
            reason=reason,
            details=details,
            conversation_id=conversation_id
        )
        self.audit.log(
            event_type="HUMAN_ESCALATION_CREATED",
            actor="agent",
            details=f"Escalation {esc_id} ({category}) for {customer_key}: {reason}"
        )
        return {
            "escalation_id": esc_id,
            "category": category,
            "reason": reason,
            "status": "pending",
            "details": details
        }

    def get_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.repo.get_all(limit)

    def get_by_customer(self, customer_key: str) -> List[Dict[str, Any]]:
        return self.repo.get_by_customer(customer_key)
