# System Architecture — Customer Resolution Agent

## AI-Powered Airline Customer Support System

---

## 1. Complete System Architecture Diagram (Mermaid)

```mermaid
flowchart TD
    %% Styling Definitions
    classDef clientLayer fill:#EBF5FF,stroke:#2563EB,stroke-width:2px,color:#1E3A8A;
    classDef deployLayer fill:#F3E8FF,stroke:#7C3AED,stroke-width:2px,color:#4C1D95;
    classDef apiLayer fill:#ECFDF5,stroke:#059669,stroke-width:2px,color:#064E3B;
    classDef logicLayer fill:#FEF3C7,stroke:#D97706,stroke-width:2px,color:#78350F;
    classDef aiLayer fill:#FCE7F3,stroke:#DB2777,stroke-width:2px,color:#831843;
    classDef dbLayer fill:#F1F5F9,stroke:#475569,stroke-width:2px,color:#0F172A;

    %% 1. Presentation Layer
    subgraph Presentation_Layer ["1. Presentation Layer (Browser Client)"]
        User(["👤 Airline Passenger / Reviewer"])
        UI_HTML["HTML5 Interface\n(templates/index.html)"]
        UI_CSS["CSS3 Styling & Layout\n(static/style.css)"]
        UI_JS["JavaScript Client Controller\n(static/app.js)"]
    end
    class Presentation_Layer,UI_HTML,UI_CSS,UI_JS clientLayer;

    %% 2. Deployment & Hosting Layer
    subgraph Deployment_Layer ["2. Deployment & Server Hosting Layer"]
        Render["Render Cloud Web Service (Free Tier)\nLinux Container Runtime: Python 3.11.9"]
        Gunicorn["Gunicorn WSGI Server\n(gunicorn app:app / Procfile)"]
    end
    class Deployment_Layer,Render,Gunicorn deployLayer;

    %% 3. Backend & API Layer
    subgraph API_Layer ["3. Backend & API Routing Layer (Flask 3.1.0)"]
        FlaskCore["Flask Application Factory\n(app/__init__.py / app.py)"]
        AppConfig["Environment Config & Secrets Manager\n(app/config.py)"]
        
        subgraph Blueprints ["Flask Blueprints (app/api/)"]
            Route_Chat["POST /api/chat"]
            Route_Cust["GET /api/customers\nGET /api/conversation/:id"]
            Route_Action["POST /api/action/confirm\nPOST /api/action/cancel"]
            Route_Esc["GET /api/escalations"]
            Route_Sys["GET /api/system/status\nGET /api/policies"]
        end
    end
    class API_Layer,FlaskCore,AppConfig,Blueprints,Route_Chat,Route_Cust,Route_Action,Route_Esc,Route_Sys apiLayer;

    %% 4. Application Logic & Safety Layer
    subgraph Logic_Layer ["4. Application Logic & Policy Guardrails Layer"]
        ConvMgr["Conversation Manager\n(app/agents/conversation_manager.py)\nMulti-Turn State & Context Tracking"]
        
        DecEngine["Agent Decision Engine\n(app/agents/decision_engine.py)\nSynthesizes Intent & Business Rules"]
        
        PolEngine["Deterministic Policy Engine\n(app/policies/policy_engine.py)\nStrict Assignment 3 Rule Guardrails"]
        
        ToolReg["Python Tool Calling Layer\n(app/tools/registry.py)\nbooking_tools | action_tools | escalation_tools"]
        
        ActSvc["Action Lifecycle Manager\n(app/services/action_service.py)\nproposed ➔ awaiting_confirmation ➔ executed"]
        
        EscSvc["Supervisor Escalation Service\n(app/services/escalation_service.py)\nTickets: Legal, Upgrades, Waivers > ₹1,500"]
    end
    class Logic_Layer,ConvMgr,DecEngine,PolEngine,ToolReg,ActSvc,EscSvc logicLayer;

    %% 5. AI Integration Layer
    subgraph AI_Layer ["5. AI Integration & Language Understanding Layer"]
        EnvSecrets["Secure Environment Variables\n(.env / Render Dashboard Secrets)\nGROQ_API_KEY (Hidden & Protected)"]
        
        Factory["AI Provider Factory\n(app/ai/provider_factory.py)\nAuto-detection & Seamless Fallback"]
        
        GroqProvider["Groq AI Provider\n(app/ai/groq_provider.py)\nModel: llama-3.3-70b-versatile\nStructured JSON Intent Schema"]
        
        LocalProvider["Deterministic Local Engine\n(app/ai/local_fallback_provider.py)\nZero-Dependency Offline NLP Engine"]
        
        GroqAPI[("🌐 External Groq Cloud API\nhttps://api.groq.com/openai/v1/chat/completions\n(OpenAI-Compatible Chat Endpoint)")]
    end
    class AI_Layer,EnvSecrets,Factory,GroqProvider,LocalProvider,GroqAPI aiLayer;

    %% 6. Database Layer
    subgraph Database_Layer ["6. Database Persistence Layer (SQLite3)"]
        DB_Conn["Database Connector & Migrations\n(app/database/connection.py)"]
        DB_Seed["Auto-Seed Initializer\n(app/database/seed_data.py)\nPriya (Gold) | Arvind (Silver) | Meher (Platinum)"]
        
        DB_File[("SQLite Database\n(conversation.db)")]
        
        subgraph Tables ["Database Tables"]
            T_Cust["customers\nbookings\nflights"]
            T_Msg["conversations\nmessages\nagent_decisions"]
            T_Gov["actions\nescalations\naudit_logs\npolicies"]
        end
    end
    class Database_Layer,DB_Conn,DB_Seed,DB_File,Tables,T_Cust,T_Msg,T_Gov dbLayer;

    %% Connections and Flow
    User -->|"1. Types message / selects scenario"| UI_HTML
    UI_HTML --- UI_CSS
    UI_HTML --> UI_JS
    UI_JS -->|"2. HTTP POST JSON /api/chat"| Render
    Render --> Gunicorn
    Gunicorn --> FlaskCore
    FlaskCore --> Route_Chat
    
    Route_Chat --> ConvMgr
    ConvMgr -->|"3. Request intent & sentiment"| Factory
    
    EnvSecrets -.->|"Supplies secret GROQ_API_KEY"| AppConfig
    AppConfig -.-> Factory
    
    Factory -->|"If API key configured"| GroqProvider
    Factory -->|"If offline / no key"| LocalProvider
    
    GroqProvider -->|"4. HTTPS REST POST\nBearer Authorization"| GroqAPI
    GroqAPI -->|"5. Structured JSON Intent\n(intent, emotion, urgency)"| GroqProvider
    GroqProvider --> ConvMgr
    LocalProvider --> ConvMgr
    
    ConvMgr -->|"6. Intent + History"| DecEngine
    DecEngine <-->|"7. Validate against PDF rules\n(Cannot be bypassed by LLM)"| PolEngine
    
    DecEngine -->|"8. Trigger validated Python tools"| ToolReg
    ToolReg --> ActSvc
    ToolReg --> EscSvc
    
    ActSvc <-->|"9. Check idempotency & record status"| DB_Conn
    EscSvc <-->|"10. Log supervisor tickets"| DB_Conn
    ConvMgr <-->|"11. Save turn & audit logs"| DB_Conn
    
    DB_Conn --- DB_File
    DB_File --- Tables
    DB_Seed -.->|"Auto-populates initial records"| DB_File
    
    DecEngine -->|"12. Formatted grounded reply"| ConvMgr
    ConvMgr -->|"13. JSON Response (reply, action, telemetry)"| Route_Chat
    Route_Chat --> Gunicorn
    Gunicorn --> Render
    Render -->|"14. HTTP 200 JSON Payload"| UI_JS
    UI_JS -->|"15. Renders chat bubble & action cards"| UI_HTML
    UI_HTML -->|"16. Passenger receives grounded answer"| User
```

---

## 2. Technology Stack Breakdown

| Layer | Technologies & Tools Actually Used |
| :--- | :--- |
| **Frontend / Presentation** | HTML5, CSS3 (Aviation theme, CSS grid/flexbox), Vanilla JavaScript (ES6+ fetch API) |
| **Server & Hosting** | Render Web Service (Free tier container), Gunicorn 26.2.0 WSGI server, Python 3.11.9 runtime |
| **Backend Framework** | Python 3.11 / 3.13, Flask 3.1.0, Flask Blueprints (`app/api/`), `pathlib` path resolution |
| **Application Logic** | Custom Agent Architecture (`ConversationManager`, `DecisionEngine`, `PolicyEngine`, `ActionService`) |
| **AI Integration** | Groq Cloud API (`llama-3.3-70b-versatile` via OpenAI-compatible `/v1/chat/completions`), `requests` library |
| **Offline Fallback** | Deterministic Local Reasoning Engine (`LocalFallbackProvider`), 0 external API dependencies |
| **Security & Secrets** | `python-dotenv` (`.env`), Render Environment Variables, `.gitignore` credential masking |
| **Database & ORM** | SQLite3 (`conversation.db`), raw SQL with parameters, connection pooling, auto-seeding |
| **Testing** | Pytest 9.1.1, Pytest-Cov 7.1.0 (23 unit and scenario test cases, 100% pass) |

---

## 3. End-to-End Customer Query Request-Response Workflow

```
Step 1 (Customer Action):
The passenger (e.g., Priya Nair) opens the web console, selects her profile, and enters:
"I am furious. My flight was cancelled. I want a full cash refund plus a free upgrade to business class on my return flight."

Step 2 (Browser / Client Dispatch):
static/app.js packages the message, customer ID ("priya"), and session state into a JSON payload and dispatches an asynchronous HTTP POST request to /api/chat.

Step 3 (Web Server & Gateway):
Render routes the request to the Gunicorn WSGI process, which passes the request to the Flask application instance created via the application factory in app/__init__.py.

Step 4 (API Routing & History Retrieval):
The route handler in app/api/chat_routes.py invokes ConversationManager.handle_message(). It loads the passenger's conversation history and disruption facts from SQLite.

Step 5 (AI Integration & Intent Parsing):
ProviderFactory retrieves the GROQ_API_KEY stored securely in environment variables (never exposed in source code or to the browser). It sends a REST request to Groq's OpenAI-compatible endpoint:
https://api.groq.com/openai/v1/chat/completions
Groq analyzes the query and returns structured JSON specifying:
- Primary Intent: refund_request
- Secondary Intent: upgrade_request
- Emotion: furious
- Urgency: high

Step 6 (Policy Guardrail Engine Evaluation):
The LLM output is NOT directly executed. It is passed to DecisionEngine and PolicyEngine, which enforce the strict Assignment 3 PDF rules:
- Cancellation Policy (POL-CANCEL-01): Entitled to full refund within 7 business days to original payment method, or free 24-hour rebooking.
- Loyalty Policy (POL-LOYALTY-01): Gold tier grants priority rebooking, but explicitly prohibits complimentary cabin upgrades.
- Mandatory Escalation (POL-PROHIBIT-01): The unauthorized business-class upgrade request is intercepted and converted into a human supervisor ticket.

Step 7 (Safe Tool & Database Execution):
- The agent calls create_refund_request() via the ToolRegistry, placing the refund action in "awaiting_confirmation" status.
- The agent calls create_escalation(), recording a supervisor ticket under category "unauthorized_compensation".
- Idempotency keys prevent duplicate refund records.
- Dialogue turns and audit events are saved to conversation.db.

Step 8 (Response Transmission & Rendering):
The Flask backend returns HTTP 200 with the synthesized response, cited policy IDs, and telemetry. static/app.js renders:
- An empathetic agent message explaining policy limits.
- An interactive Action Confirmation Card with [✓ Approve & Execute] and [✗ Decline] buttons.
- A notification badge showing that the upgrade request was escalated to a supervisor.
- Updated telemetry in the inspector panel.
```
