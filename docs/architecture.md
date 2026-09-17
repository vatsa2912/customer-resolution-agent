# System Architecture & Technical Specification

## 1. Architectural Overview

AeroResolve AI is an autonomous, policy-grounded AI Customer Support Platform designed for high-stakes airline disruption management. It replaces static keyword matching with a multi-layered agent architecture that decouples **natural-language understanding** from **deterministic policy enforcement** and **safe action execution**.

```
                           ┌─────────────────────────────────┐
                           │      Web Browser Client         │
                           │  (HTML5 / CSS3 / JavaScript)    │
                           └────────────────┬────────────────┘
                                            │ HTTP / JSON
                                            ▼
                           ┌─────────────────────────────────┐
                           │        Flask REST API           │
                           │  (Blueprints / CORS / Routing)  │
                           └────────────────┬────────────────┘
                                            │
                                            ▼
                           ┌─────────────────────────────────┐
                           │   Conversation Manager Layer    │
                           │  - Multi-turn state tracking    │
                           │  - Pending action detection     │
                           └────────────────┬────────────────┘
                                            │
                  ┌─────────────────────────┴─────────────────────────┐
                  ▼                                                   ▼
┌────────────────────────────────────┐             ┌────────────────────────────────────┐
│      AI Provider Abstraction       │             │     Deterministic Policy Engine    │
│  - Gemini / Groq / OpenRouter      │             │  - Strict Assignment 3 PDF Rules   │
│  - Ollama / Local Fallback         │             │  - Ground Truth Validation         │
│  - Structured Intent & Emotion     │             │  - Prohibited Action Guardrails    │
└─────────────────┬──────────────────┘             └──────────────────┬─────────────────┘
                  │                                                   │
                  └─────────────────────────┬─────────────────────────┘
                                            │
                                            ▼
                           ┌─────────────────────────────────┐
                           │     Agent Decision Engine       │
                           │  - Rule synthesis               │
                           │  - Customer response generation │
                           │  - Two-stage confirmation check │
                           └────────────────┬────────────────┘
                                            │
                  ┌─────────────────────────┴─────────────────────────┐
                  ▼                                                   ▼
┌────────────────────────────────────┐             ┌────────────────────────────────────┐
│      Action Execution Service      │             │     Human Escalation Service       │
│  - Lifecycle: Proposed ➔ Confirmed │             │  - Supervisor Ticket Queue         │
│  - Idempotency validation          │             │  - Category & Urgency classification│
│  - Simulated execution labeling    │             │  - Audit Trail Logging             │
└─────────────────┬──────────────────┘             └──────────────────┬─────────────────┘
                  │                                                   │
                  └─────────────────────────┬─────────────────────────┘
                                            │
                                            ▼
                           ┌─────────────────────────────────┐
                           │     SQLite Persistence Layer    │
                           │  - Customers, Bookings, Flights │
                           │  - Conversations & Messages     │
                           │  - Actions, Escalations, Audit  │
                           └─────────────────────────────────┘
```

---

## 2. Core Components

### 2.1 AI Provider Abstraction (`app/ai/`)
The system isolates LLM dependencies behind an abstract interface (`BaseAIProvider`).
- **`ProviderFactory`**: Dynamically instantiates the target provider based on environment variables (`AI_PROVIDER`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `OLLAMA_BASE_URL`).
- **`LocalFallbackProvider`**: A zero-dependency, deterministic offline reasoning engine that extracts structured intents, emotions, urgency, and entities. This guarantees 100% test reliability and instant local demonstration without external network access or paid API keys.
- **`GeminiProvider`**: Direct HTTPS REST integration with Google Gemini (`gemini-1.5-flash` / `gemini-2.5-flash`) with structured JSON schema output.
- **`GroqProvider`**: Ultra-fast OpenAI-compatible chat completion provider powered by Llama 3.3.
- **`OpenRouterProvider` & `OllamaProvider`**: Universal cloud and local offline LLM endpoints.

### 2.2 Grounded Policy Engine (`app/policies/`)
The LLM is **never** permitted to directly execute actions, invent benefits, or make policy exceptions. The Deterministic Policy Engine acts as an impenetrable guardrail layer enforcing the Assignment 3 rules:
1. **Cancellation (`POL-CANCEL-01`)**: Airline-caused cancellations entitle customers to free rebooking within 24 hours OR full refund.
2. **Delay Compensation (`POL-DELAY-01/02/03`)**:
   - `< 3 hours`: ₹500 meal voucher.
   - `3 - 5 hours`: Meal voucher + lounge access.
   - `> 5 hours`: Meal voucher + lounge access + hotel accommodation for *delayed hours only* (NOT a full night).
3. **Refund Processing (`POL-REFUND-01`)**: Processed within 7 business days to *original payment method only*.
4. **Fare Difference (`POL-FARE-01`)**: Voluntary higher-fare rebooking requires paying fare difference. Agents can waive up to ₹1,500; above ₹1,500 strictly requires supervisor approval.
5. **Loyalty Perks (`POL-LOYALTY-01`)**: Gold and Platinum members receive priority rebooking (first access to next-available seats), but *no extra monetary or cabin class compensation*.
6. **Mandatory Human Escalation (`POL-PROHIBIT-01`)**: Immediate escalation triggers for legal threats, formal complaints, requests for out-of-policy cash/upgrades, and fare waivers > ₹1,500.

### 2.3 Safe Action Lifecycle & State Machine (`app/services/action_service.py`)
To prevent accidental or unauthorized actions, irreversible requests (refunds, rebookings) follow an explicit state machine:

```
[ Customer Inquiry ] ──▶ [ Agent Proposes Action ] ──▶ [ Status: awaiting_confirmation ]
                                                                   │
                                       ┌───────────────────────────┴───────────────────────────┐
                                       ▼                                                       ▼
                            [ Customer Confirms ]                                    [ Customer Declines ]
                                       │                                                       │
                                       ▼                                                       ▼
                             [ Idempotency Check ]                                    [ Status: rejected ]
                                       │
                                       ▼
                             [ Status: executed ]
                   [ Simulated Execution — Educational Prototype ]
```

- **Idempotency**: Every action is keyed by `{customer_key}_{action_type}_{flight_number}`. Re-proposing or executing the same action returns the existing record rather than generating duplicates.

---

## 3. Database Schema

The upgraded SQLite database (`conversation.db`) models 10 distinct entities:
- `customers`: Primary customer records (Priya Nair, Arvind Kulkarni, Meher Kaur), contact info, loyalty tier, and travel complaint history.
- `bookings`: PNR booking references linked to customers.
- `flights`: Flight segments, routes, scheduled departures, new departures, status, disruption reasons, and delay hours.
- `policies`: Formal airline rules, descriptions, citations, and JSON configuration.
- `conversations`: Conversation sessions per customer.
- `messages`: Multi-turn customer and agent dialogue history, detected intent, and metadata (cited policies, model used).
- `agent_decisions`: Recorded decision telemetry, rationale, guardrail outcomes.
- `actions`: Action lifecycle records (`proposed`, `awaiting_confirmation`, `executed`, `rejected`).
- `escalations`: Supervisor escalation tickets, categories, reasons, and review status.
- `audit_logs`: Append-only event stream tracking every critical agent and customer action.
