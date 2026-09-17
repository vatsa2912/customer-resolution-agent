# REST API Documentation

The AeroResolve AI system provides a clean, modular REST API for chat interactions, customer lookups, action lifecycle management, and telemetry.

Base URL: `http://127.0.0.1:5000/api`

---

## 1. Chat & Conversation

### `POST /api/chat`
Dispatches a customer message to the autonomous agent.

**Request Body**:
```json
{
  "customer_key": "priya",
  "message": "I want a refund for my cancelled flight."
}
```

**Response (200 OK)**:
```json
{
  "reply": "Your flight SK-204 was cancelled due to operational reasons. Under airline policy, you are entitled to a full refund to your original payment method, processed within 7 business days. Would you like me to initiate this refund request now?",
  "intent": "refund_request",
  "decision": "propose_refund_awaiting_confirmation",
  "policies_cited": [
    "POL-CANCEL-01",
    "POL-REFUND-01"
  ],
  "action": {
    "action_id": 1,
    "action_type": "refund_request",
    "status": "awaiting_confirmation",
    "details": "Full cash refund for cancelled flight SK-204 (Delhi → Goa) processed within 7 business days to original payment method.",
    "requires_confirmation": true
  },
  "escalation": null,
  "escalated": false,
  "requires_confirmation": true,
  "reason": "Refund proposed; awaiting explicit customer confirmation.",
  "provider_used": "local",
  "model_used": "deterministic-engine"
}
```

---

## 2. Action Management

### `POST /api/action/confirm`
Confirms and executes a pending action that was awaiting customer approval.

**Request Body**:
```json
{
  "action_id": 1
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "action_id": 1,
  "status": "executed",
  "action_type": "refund_request",
  "details": "Full cash refund for cancelled flight SK-204 (Delhi → Goa) processed within 7 business days to original payment method. [Simulated Execution — Educational Prototype]",
  "message": "Action successfully confirmed and executed."
}
```

### `POST /api/action/cancel`
Cancels an action in `awaiting_confirmation` status.

**Request Body**:
```json
{
  "action_id": 1,
  "reason": "Customer declined refund"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "action_id": 1,
  "status": "rejected",
  "message": "Action cancelled as requested."
}
```

---

## 3. Customer & Session Management

### `GET /api/customers`
Retrieves all customer profiles, bookings, and flight records from the Assignment 3 Data Pack.

### `GET /api/conversation/<customer_key>`
Retrieves message history, recorded actions, pending action, and escalations for a specific customer (`priya`, `arvind`, `meher`).

### `POST /api/conversation/<customer_key>/clear`
Clears chat, action, and escalation history for the specified customer to restart a clean demonstration session.

---

## 4. Telemetry & Governance

### `GET /api/escalations`
Returns all active and historical supervisor escalation tickets.

### `GET /api/policies`
Returns all 7 grounded service policies from the Assignment 3 Data Pack.

### `GET /api/system/status`
Returns active AI provider health, model name, and database status.
