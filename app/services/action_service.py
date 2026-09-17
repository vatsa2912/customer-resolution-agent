from typing import Dict, Any, Optional
from app.database.repositories import ActionRepository, CustomerRepository, AuditRepository

class ActionService:
    def __init__(self, action_repo: Optional[ActionRepository] = None, cust_repo: Optional[CustomerRepository] = None):
        self.action_repo = action_repo or ActionRepository()
        self.cust_repo = cust_repo or CustomerRepository()
        self.audit_repo = AuditRepository()

    def propose_action(
        self,
        customer_key: str,
        action_type: str,
        details: str,
        idempotency_key: str,
        requires_confirmation: bool = True,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Creates an action in 'awaiting_confirmation' status if confirmation required,
        otherwise directly executes it. Returns existing action if idempotency key exists.
        """
        # Check idempotency first
        existing = self.action_repo.get_by_idempotency(idempotency_key)
        if existing:
            is_done = existing["status"] in ("executed", "approved")
            return {
                "action_id": existing["id"],
                "status": existing["status"],
                "action_type": existing["action_type"],
                "details": existing["details"],
                "already_executed": is_done,
                "requires_confirmation": existing["status"] == "awaiting_confirmation",
                "message": "This request has already been recorded previously."
            }

        initial_status = "awaiting_confirmation" if requires_confirmation else "executed"
        action_id = self.action_repo.create(
            customer_key=customer_key,
            action_type=action_type,
            status=initial_status,
            details=details,
            idempotency_key=idempotency_key,
            conversation_id=conversation_id
        )

        self.audit_repo.log(
            event_type="ACTION_PROPOSED" if requires_confirmation else "ACTION_EXECUTED",
            actor="agent",
            details=f"Action {action_type} (ID {action_id}) for {customer_key} in status {initial_status}"
        )

        return {
            "action_id": action_id,
            "status": initial_status,
            "action_type": action_type,
            "details": details,
            "requires_confirmation": requires_confirmation,
            "already_executed": False
        }

    def confirm_action(self, action_id: int) -> Dict[str, Any]:
        """
        Executes an action that was in awaiting_confirmation status.
        """
        action = self.action_repo.get_by_id(action_id)
        if not action:
            return {"success": False, "error": f"Action {action_id} not found."}

        if action["status"] == "executed":
            return {
                "success": True,
                "action_id": action_id,
                "status": "executed",
                "details": action["details"],
                "message": "This action was already confirmed and executed."
            }

        if action["status"] != "awaiting_confirmation":
            return {
                "success": False,
                "error": f"Cannot execute action in status '{action['status']}'."
            }

        simulated_details = f"{action['details']} [Simulated Execution — Educational Prototype]"
        self.action_repo.update_status(action_id, status="executed", details=simulated_details)

        self.audit_repo.log(
            event_type="ACTION_CONFIRMED_AND_EXECUTED",
            actor="customer_and_backend",
            details=f"Action {action['action_type']} (ID {action_id}) executed successfully"
        )

        return {
            "success": True,
            "action_id": action_id,
            "status": "executed",
            "action_type": action["action_type"],
            "details": simulated_details,
            "message": "Action successfully confirmed and executed."
        }

    def cancel_action(self, action_id: int, reason: str = "Cancelled by customer") -> Dict[str, Any]:
        action = self.action_repo.get_by_id(action_id)
        if not action:
            return {"success": False, "error": f"Action {action_id} not found."}

        if action["status"] == "executed":
            return {"success": False, "error": "Cannot cancel an action that has already executed."}

        self.action_repo.update_status(action_id, status="rejected", details=f"{action['details']} (Cancelled: {reason})")
        self.audit_repo.log(
            event_type="ACTION_CANCELLED",
            actor="customer",
            details=f"Action {action_id} cancelled: {reason}"
        )
        return {
            "success": True,
            "action_id": action_id,
            "status": "rejected",
            "message": "Action cancelled as requested."
        }

    def get_pending_action(self, customer_key: str) -> Optional[Dict[str, Any]]:
        return self.action_repo.get_latest_pending(customer_key)
