# AeroResolve AI — Autonomous Customer Resolution Agent

Live Application Link: [https://your-deployed-app-link.com](https://customer-resolution-agent-1.onrender.com/)

[![Tests: Pytest](https://img.shields.io/badge/Tests-15%20Passed-success.svg)](file:///tests)
[![Python: 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Framework: Flask](https://img.shields.io/badge/Framework-Flask%203.1-black.svg)](https://flask.palletsprojects.com)
[![Status: Reviewer--Ready](https://img.shields.io/badge/Prototype-AIONOS%20Assignment%203-blueviolet.svg)](#)

A production-grade, policy-grounded autonomous AI customer support system for high-stakes airline disruption management. Built for **Assignment 3 (Customer-Facing Resolution Agent)** and strictly grounded in the official Airline Disruption Data Pack.

---

## 1. System Highlights & What Was Improved

The original implementation relied on brittle keyword matching (`if "refund" in message`), instantly executed database mutations without user confirmation, lacked multi-turn context memory, and had no real LLM or AI provider integration.

**Key Upgrades:**
1. **Real AI Agent Architecture**: Replaced fixed keywords with structured natural-language intent and entity extraction supporting multiple AI providers (Gemini, Groq, OpenRouter, Ollama, and an intelligent zero-dependency Local Fallback).
2. **Deterministic Policy Guardrail Engine**: Decouples natural-language reasoning from policy enforcement. The LLM cannot invent airline policy or approve prohibited actions; all decisions are strictly validated against the Assignment 3 rules.
3. **Safe Action Execution Lifecycle**: Implements a strict state machine (`proposed` ➔ `awaiting_confirmation` ➔ `approved` ➔ `executed` / `rejected`). Irreversible actions (refunds, rebookings) require explicit customer confirmation before execution, protected by idempotency keys to prevent duplicate requests.
4. **Supervisor Escalation Center**: Automatically flags and routes prohibited requests (complimentary upgrades, fare difference waivers > ₹1,500, legal threats, formal complaints) to a dedicated supervisor review queue.
5. **Multi-Turn Context & Conversational Memory**: Preserves context, remembers customer identities, flights, and handles natural-language confirmations ("yes", "confirm", "proceed", or clicking UI buttons).
6. **Modern Reviewer Console**: A responsive 3-panel airline operations interface with customer cards, interactive in-chat action confirmation cards, live decision telemetry, and real-time inspector tabs.
7. **Comprehensive Test Suite**: 15 automated pytest tests covering policy edge cases, action lifecycles, intent parsing, and end-to-end assignment scenarios.

---

## 2. Tech Stack

- **Backend**: Python 3.13, Flask 3.1.0, SQLite3
- **AI Providers**: Google Gemini REST API, Groq OpenAI-compatible API, OpenRouter, Ollama, and Deterministic Local Fallback
- **Frontend**: Responsive HTML5, Modern CSS3 with aviation theme, Vanilla JavaScript (zero heavy frontend build steps)
- **Testing**: Pytest 9.1

---

## 3. Quick Start (One-Command Run)

The application runs **100% out of the box** using the built-in deterministic local intelligence engine—**no external API keys or payments are required**.

### Windows PowerShell

```powershell
# 1. Clone or navigate to the repository
cd customer_resolution_agent

# 2. Activate existing virtual environment (or create one)
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the application
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 4. AI Provider Setup (Optional)

The application features a modular AI provider abstraction (`app/ai/`). If you wish to connect an external LLM, copy `.env.example` to `.env` and set your key:

```powershell
copy .env.example .env
```

Edit `.env`:

```env
# Choose provider: auto | gemini | groq | openrouter | ollama | local
AI_PROVIDER=auto

# Option A: Google Gemini Free Tier
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Option B: Groq Free Tier
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Option C: OpenRouter Free Models
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free

# Option D: Local Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

> [!NOTE]
> When `AI_PROVIDER=auto`, the system automatically detects available API keys. If no key is set, it seamlessly activates the `LocalFallbackProvider` with zero errors.

---

## 5. Automated Tests

Run the full automated test suite:

```powershell
.\.venv\Scripts\pytest tests/ -v
```

**Test Coverage Summary:**
- `tests/test_policies.py`: Evaluates cancellation eligibility, delay tiers (<3h, 3-5h, >5h), fare waiver limits (₹1,500 threshold), loyalty tier rules, and hotel coverage limitations.
- `tests/test_actions.py`: Tests proposed action creation, confirmation requirement, status transition to executed, cancellation, and idempotency prevention of duplicate actions.
- `tests/test_agent.py`: Validates flexible natural-language intent matching across diverse customer expressions, emotion detection, and unknown customer handling.
- `tests/test_scenarios.py`: Runs all three required Assignment 3 scenarios (Priya, Arvind, Meher) and legal escalation edge cases end-to-end.

---

## 6. How to Test the Three Required Scenarios

The web interface includes **1-click scenario preset buttons** in the left sidebar:

### Scenario 1 — Priya Nair (Gold, PNR: SK4821X)
1. Select **Priya Nair — Gold Tier** in the dropdown.
2. Click **Scenario 1: Priya: Cancelled + Angry + Business Upgrade** (or send: *"I am furious. My flight was cancelled. I want a full cash refund plus a free upgrade to business class on my return flight."*).
3. **Agent Behavior**:
   - Acknowledges Priya's frustration empathetically.
   - Notes flight SK-204 was cancelled due to operational reasons.
   - Refuses the complimentary business-class upgrade per policy (`POL-LOYALTY-01`), explaining Gold tier receives priority rebooking but no extra cabin compensation.
   - Escalates the upgrade exception request to a supervisor (`POL-PROHIBIT-01`).
   - Proposes a full refund to original payment method within 7 business days (`POL-REFUND-01`) or free priority rebooking within 24h.
   - Displays an in-chat **Action Confirmation Card**.
4. Confirm by typing *"Yes, proceed with refund"* or clicking the **✓ Approve & Execute** button.

### Scenario 2 — Arvind Kulkarni (Silver, PNR: TR1190B)
1. Select **Arvind Kulkarni — Silver Tier** in the dropdown.
2. Click **Scenario 2: Arvind: 4h Delay + Hotel Request** (or send: *"My flight is delayed by 4 hours. I missed an important meeting. I want hotel accommodation."*).
3. **Agent Behavior**:
   - Empathizes with his disruption and missed business meeting.
   - Applies eligible 4-hour delay benefits: **meal voucher + lounge access** (`POL-DELAY-02`).
   - Explains that hotel accommodation is provided **only for delays exceeding 5 hours** (`POL-DELAY-03`), politely denying the hotel request.
   - View the issued vouchers in the **Actions** tab on the right panel.

### Scenario 3 — Meher Kaur (Platinum, PNR: WL7742)
1. Select **Meher Kaur — Platinum Tier** in the dropdown.
2. Click **Scenario 3: Meher: 6h Delay + Full Hotel + ₹2,000 Waiver** (or send: *"My flight is delayed by 6 hours. I want a full night's hotel stay. Also move me to another higher-fare flight. The fare difference is ₹2,000. I want you to waive it."*).
3. **Agent Behavior**:
   - Separates the hotel issue from the fare waiver issue.
   - Grants meal voucher, lounge access, and hotel accommodation **covering strictly the delayed hours** until new departure (20:00), clarifying that a *full night's stay* is not included (`POL-DELAY-03`).
   - Evaluates the ₹2,000 fare waiver against policy `POL-FARE-01` (agent limit ₹1,500).
   - Escalates the waiver request to a supervisor because it exceeds ₹1,500 (`POL-PROHIBIT-01`).
   - View the escalation ticket in the **Escalations** tab.

### Edge Case: Legal Threats / Formal Complaints
- Type: *"This is unacceptable. I am going to file a formal complaint and take legal action over this."*
- **Agent Behavior**: Immediately de-escalates and routes the conversation to the specialist support team without debate.

---

## 7. Project Structure

```text
customer_resolution_agent/
├── app.py                      # Flask entry point & application runner
├── requirements.txt            # Production dependencies
├── pytest.ini                  # Pytest configuration
├── .env.example                # Sample environment variables
├── .gitignore                  # Git exclusions (credentials, caches, db)
├── README.md                   # Primary documentation
│
├── app/                        # Modular application package
│   ├── __init__.py             # Application factory (create_app)
│   ├── config.py               # Central environment configuration
│   │
│   ├── api/                    # REST API Blueprints
│   │   ├── __init__.py         # Blueprint root
│   │   ├── chat_routes.py      # POST /api/chat
│   │   ├── customer_routes.py  # Customer & session endpoints
│   │   ├── action_routes.py    # Action confirm/cancel endpoints
│   │   ├── escalation_routes.py# Supervisor queue endpoints
│   │   └── system_routes.py    # Policies and system health telemetry
│   │
│   ├── ai/                     # AI Provider Abstraction
│   │   ├── base_provider.py    # Abstract base interface
│   │   ├── gemini_provider.py  # Google Gemini REST provider
│   │   ├── groq_provider.py    # Groq OpenAI-compatible provider
│   │   ├── openrouter_provider.py
│   │   ├── ollama_provider.py  # Local Ollama provider
│   │   ├── local_fallback_provider.py # Intelligent offline reasoning engine
│   │   └── provider_factory.py # Dynamic provider factory
│   │
│   ├── policies/               # Grounded Policy Knowledge Layer
│   │   ├── policy_data.py      # Canonical policy rules from PDF
│   │   └── policy_engine.py    # Deterministic rule & guardrail engine
│   │
│   ├── tools/                  # Safe Tool Layer
│   │   ├── registry.py         # Tool registry & schema decorator
│   │   ├── booking_tools.py    # Profile, PNR, flight status tools
│   │   ├── policy_tools.py     # Policy evaluation tools
│   │   ├── action_tools.py     # Safe action proposing tools
│   │   └── escalation_tools.py # Supervisor escalation tools
│   │
│   ├── services/               # Core Business Logic Services
│   │   ├── action_service.py   # State machine, confirmation, idempotency
│   │   ├── escalation_service.py # Supervisor queue management
│   │   └── audit_service.py    # Append-only audit logger
│   │
│   ├── database/               # Data Persistence Layer
│   │   ├── connection.py       # SQLite connection & schema migrations
│   │   ├── models.py           # Domain dataclasses
│   │   ├── repositories.py     # Repository data access layer
│   │   └── seed_data.py        # PDF seed data auto-populator
│   │
│   └── agents/                 # Multi-Turn Agent Framework
│       ├── prompts.py          # Strict system instructions
│       ├── decision_engine.py  # Reasoning & policy synthesis engine
│       ├── conversation_manager.py # Context coordinator
│       └── resolution_agent.py # High-level agent interface
│
├── templates/
│   └── index.html              # Responsive 3-panel reviewer console
├── static/
│   ├── style.css               # Aviation-themed styling
│   └── app.js                  # Client controller & telemetry renderer
├── tests/
│   ├── test_policies.py        # Policy engine test cases
│   ├── test_actions.py         # Action lifecycle & idempotency tests
│   ├── test_agent.py           # Intent extraction & NLP tests
│   └── test_scenarios.py       # End-to-end scenario verification
└── docs/
    ├── architecture.md         # Full architectural specification
    ├── demo_script.md          # Reviewer step-by-step walkthrough
    └── api.md                  # REST API documentation
```

---

## 8. Safety & Policy Compliance

- **No Arbitrary Code Execution**: No `eval()` or dangerous deserialization on model output.
- **Strict Scope Boundaries**: The agent uses only the 3 supplied customers and official service rules. It never invents flight availability, hotel names, or compensation amounts.
- **Transparent Simulation**: All recorded actions are explicitly tagged as `[Simulated Execution — Educational Prototype]`.
- **Zero Hallucination of Authority**: The LLM cannot authorize refunds, waivers, or compensation directly; actions must be evaluated and approved by the deterministic backend engine.

---

## 9. Known Limitations & Future Roadmap

- **Prototype Scope**: External airline systems (SABRE/Amadeus) and real payment gateways are simulated in SQLite.
- **Future Enhancements**: Integration with live flight status webhooks, voice agent support via WebRTC, and multi-lingual customer support.
