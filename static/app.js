// AeroResolve AI Client Application
document.addEventListener("DOMContentLoaded", () => {
  const customerSelect = document.getElementById("customer-select");
  const profileCard = document.getElementById("profile-card");
  const flightCard = document.getElementById("flight-card");
  const chatMessages = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const btnSend = document.getElementById("btn-send");
  const typingIndicator = document.getElementById("typing-indicator");
  const btnResetSession = document.getElementById("btn-reset-session");
  const chatCustomerName = document.getElementById("chat-customer-name");
  const chatBookingTag = document.getElementById("chat-booking-tag");
  const aiStatusPill = document.getElementById("ai-status-pill");
  const aiProviderText = document.getElementById("ai-provider-text");

  // Tabs & Inspectors
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  const actionsList = document.getElementById("actions-list");
  const escalationsList = document.getElementById("escalations-list");
  const policiesList = document.getElementById("policies-list");
  const countActions = document.getElementById("count-actions");
  const countEscalations = document.getElementById("count-escalations");

  // Telemetry elements
  const telProvider = document.getElementById("tel-provider");
  const telModel = document.getElementById("tel-model");
  const telIntent = document.getElementById("tel-intent");
  const telEmotion = document.getElementById("tel-emotion");
  const telDecision = document.getElementById("tel-decision");
  const telPolicies = document.getElementById("tel-policies");
  const telRationale = document.getElementById("tel-rationale");

  let customersData = {};
  let currentCustomerKey = "priya";

  // Tab switching
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const target = document.getElementById(`tab-${btn.dataset.tab}`);
      if (target) target.classList.add("active");
    });
  });

  // Enter to send (Shift+Enter for newline)
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Reset Session
  btnResetSession.addEventListener("click", async () => {
    if (confirm(`Reset all conversation, action, and escalation history for ${customersData[currentCustomerKey]?.name || currentCustomerKey}?`)) {
      await fetch(`/api/conversation/${currentCustomerKey}/clear`, { method: "POST" });
      await loadConversation(currentCustomerKey);
    }
  });

  // Scenario Buttons
  document.querySelectorAll(".scenario-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const scenario = btn.dataset.scenario;
      if (scenario === "scenario1") {
        customerSelect.value = "priya";
        handleCustomerChange("priya");
        chatInput.value = "I am furious. My flight was cancelled. I want a full cash refund plus a free upgrade to business class on my return flight.";
      } else if (scenario === "scenario2") {
        customerSelect.value = "arvind";
        handleCustomerChange("arvind");
        chatInput.value = "My flight is delayed by 4 hours. I missed an important meeting. I want hotel accommodation.";
      } else if (scenario === "scenario3") {
        customerSelect.value = "meher";
        handleCustomerChange("meher");
        chatInput.value = "My flight is delayed by 6 hours. I want a full night's hotel stay. Also move me to another higher-fare flight. The fare difference is ₹2,000. I want you to waive it.";
      } else if (scenario === "legal") {
        chatInput.value = "This is completely unacceptable. I am going to file a formal complaint and take legal action over this.";
      }
      chatInput.focus();
    });
  });

  // Customer Select Change
  customerSelect.addEventListener("change", (e) => {
    handleCustomerChange(e.target.value);
  });

  function handleCustomerChange(key) {
    currentCustomerKey = key;
    renderProfileAndFlight(key);
    loadConversation(key);
  }

  // Render Customer & Flight Cards
  function renderProfileAndFlight(key) {
    const cust = customersData[key];
    if (!cust) return;

    chatCustomerName.textContent = `Support: ${cust.name}`;
    chatBookingTag.textContent = `PNR: ${cust.pnr}`;

    profileCard.innerHTML = `
      <div class="cust-name">
        <span>${escapeHtml(cust.name)}</span>
        <span class="tier-badge tier-${cust.tier}">${escapeHtml(cust.tier)}</span>
      </div>
      <div class="meta-row"><strong>Booking Reference:</strong> ${escapeHtml(cust.pnr)}</div>
      <div class="meta-row"><strong>Contact:</strong> ${escapeHtml(cust.email)}</div>
      <div class="meta-row"><strong>Phone:</strong> ${escapeHtml(cust.phone)}</div>
      <div class="history-box">
        <strong>Travel History (12m):</strong> ${escapeHtml(cust.travel_history)}
      </div>
    `;

    const flights = cust.flights || [];
    let flightHtml = "";
    flights.forEach(f => {
      const isCancelled = f.status.toLowerCase().includes("cancelled");
      const isDelayed = f.status.toLowerCase().includes("delayed");
      const tagClass = isCancelled ? "tag-cancelled" : (isDelayed ? "tag-delayed" : "tag-unaffected");
      const cardClass = isCancelled ? "is-cancelled" : (isDelayed ? "is-delayed" : "");

      flightHtml += `
        <div class="flight-card ${cardClass}" style="margin-bottom: 8px;">
          <div class="flight-header">
            <span>Flight ${escapeHtml(f.flight_number)}</span>
            <span class="status-tag ${tagClass}">${escapeHtml(f.status)}</span>
          </div>
          <div class="route-desc">${escapeHtml(f.route)}</div>
          <div class="meta-row"><strong>Date:</strong> ${escapeHtml(f.date)} | <strong>Dep:</strong> ${escapeHtml(f.scheduled_departure)}</div>
          ${f.new_departure ? `<div class="meta-row" style="color: var(--warning);"><strong>New Departure:</strong> ${escapeHtml(f.new_departure)}</div>` : ""}
          ${f.reason ? `<div class="meta-row" style="color: var(--danger);"><strong>Disruption Reason:</strong> ${escapeHtml(f.reason)}</div>` : ""}
        </div>
      `;
    });

    flightCard.innerHTML = flightHtml || `<div class="empty-state">No flight records found.</div>`;
  }

  // Load Conversation & Actions
  async function loadConversation(customerKey) {
    chatMessages.innerHTML = "";
    try {
      const res = await fetch(`/api/conversation/${customerKey}`);
      const data = await res.json();

      if (!data.messages || data.messages.length === 0) {
        renderWelcomeMessage(customerKey);
      } else {
        data.messages.forEach(m => {
          appendMessage(m.sender, m.content, m.metadata, m.created_at);
        });
      }

      // If there is a pending action awaiting confirmation, render confirmation card at bottom
      if (data.pending_action) {
        renderInlineActionCard(data.pending_action);
      }

      updateInspectorLists(data.actions || [], data.escalations || []);
      scrollChatToBottom();
    } catch (err) {
      console.error("Error loading conversation:", err);
    }
  }

  function renderWelcomeMessage(customerKey) {
    const cust = customersData[customerKey];
    const custName = cust ? cust.name.split(" ")[0] : "Customer";
    const pnr = cust ? cust.pnr : "";
    const welcome = `Hello ${custName}! I am your AeroResolve Support Executive. I have retrieved your booking (${pnr}). How may I assist you with your flight disruption today?`;
    appendMessage("agent", welcome, null, null);
  }

  function appendMessage(sender, text, metadata = null, timeStr = null) {
    const row = document.createElement("div");
    row.className = `msg-row ${sender === "customer" ? "customer-row" : "agent-row"}`;

    const avatar = document.createElement("div");
    avatar.className = `avatar ${sender === "customer" ? "cust-avatar" : "agent-avatar"}`;
    avatar.textContent = sender === "customer" ? "👤" : "✈";

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";

    // Format text with markdown-style bold and newlines
    let formattedText = escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br>");

    bubble.innerHTML = `<div>${formattedText}</div>`;

    // Add policy citation tags if available
    if (metadata && metadata.policies_cited && metadata.policies_cited.length > 0) {
      const polDiv = document.createElement("div");
      polDiv.className = "policy-citations";
      metadata.policies_cited.forEach(p => {
        polDiv.innerHTML += `<span class="policy-badge">🛡️ ${escapeHtml(p)}</span>`;
      });
      bubble.appendChild(polDiv);
    }

    if (timeStr) {
      const timeSpan = document.createElement("span");
      timeSpan.className = "msg-time";
      timeSpan.textContent = timeStr.includes("T") ? timeStr.split("T")[1] : timeStr;
      bubble.appendChild(timeSpan);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    chatMessages.appendChild(row);
    scrollChatToBottom();
  }

  // Render Inline Action Confirmation Card
  function renderInlineActionCard(action) {
    const card = document.createElement("div");
    card.className = "action-card-inline";
    card.id = `action-card-${action.id}`;
    card.innerHTML = `
      <div class="action-card-header">
        <span class="action-card-title">⚠️ Action Requires Confirmation</span>
        <span class="action-card-status">${escapeHtml(action.status)}</span>
      </div>
      <div class="action-card-details">${escapeHtml(action.details)}</div>
      <div class="action-buttons-group">
        <button class="btn btn-confirm" onclick="confirmAction(${action.id})">✓ Approve & Execute</button>
        <button class="btn btn-cancel" onclick="cancelAction(${action.id})">✗ Cancel / Decline</button>
      </div>
    `;
    chatMessages.appendChild(card);
    scrollChatToBottom();
  }

  // Render Inline Escalation Card
  function renderInlineEscalationCard(esc) {
    const card = document.createElement("div");
    card.className = "escalation-card-inline";
    card.innerHTML = `
      <div class="escalation-header">
        <span>⚠️ Human Supervisor Escalation Created</span>
      </div>
      <div class="escalation-details">
        <strong>Category:</strong> ${escapeHtml(esc.category)}<br>
        <strong>Reason:</strong> ${escapeHtml(esc.reason)}
      </div>
    `;
    chatMessages.appendChild(card);
    scrollChatToBottom();
  }

  // Action Handlers
  window.confirmAction = async function(actionId) {
    const card = document.getElementById(`action-card-${actionId}`);
    if (card) {
      card.innerHTML = `<span style="color: var(--success); font-weight:600;">Processing confirmation...</span>`;
    }

    try {
      const res = await fetch("/api/action/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: actionId })
      });
      const data = await res.json();
      if (data.success) {
        appendMessage("agent", `Action confirmed: ${data.details}`, null, null);
      } else {
        appendMessage("agent", `Error executing action: ${data.error}`, null, null);
      }
      await loadConversation(currentCustomerKey);
    } catch (e) {
      console.error(e);
    }
  };

  window.cancelAction = async function(actionId) {
    const card = document.getElementById(`action-card-${actionId}`);
    if (card) card.remove();

    try {
      const res = await fetch("/api/action/cancel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: actionId })
      });
      const data = await res.json();
      if (data.success) {
        appendMessage("agent", "The proposed action was cancelled.", null, null);
      }
      await loadConversation(currentCustomerKey);
    } catch (e) {
      console.error(e);
    }
  };

  // Submit Chat Message
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;

    appendMessage("customer", message, null, "Now");
    chatInput.value = "";
    typingIndicator.classList.remove("hidden");
    btnSend.disabled = true;
    scrollChatToBottom();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_key: currentCustomerKey,
          message: message
        })
      });

      const data = await res.json();
      typingIndicator.classList.add("hidden");
      btnSend.disabled = false;

      if (data.error) {
        appendMessage("agent", `Error: ${data.error}`);
        return;
      }

      appendMessage("agent", data.reply, { policies_cited: data.policies_cited });

      if (data.action && data.requires_confirmation) {
        renderInlineActionCard(data.action);
      }

      if (data.escalation) {
        renderInlineEscalationCard(data.escalation);
      }

      // Update Telemetry
      updateTelemetry(data);

      // Refresh Inspector Actions & Escalations
      const convRes = await fetch(`/api/conversation/${currentCustomerKey}`);
      const convData = await convRes.json();
      updateInspectorLists(convData.actions || [], convData.escalations || []);

    } catch (err) {
      typingIndicator.classList.add("hidden");
      btnSend.disabled = false;
      appendMessage("agent", "Network error. Please check your connection and try again.");
      console.error(err);
    }
  });

  // Update Inspector Lists
  function updateInspectorLists(actions, escalations) {
    countActions.textContent = actions.length;
    countEscalations.textContent = escalations.length;

    // Actions list
    if (actions.length === 0) {
      actionsList.innerHTML = `<div class="empty-state">No actions recorded yet.</div>`;
    } else {
      actionsList.innerHTML = actions.map(a => `
        <div class="item-card">
          <div class="item-header">
            <strong>${escapeHtml(a.action_type)}</strong>
            <span class="item-badge status-${a.status}">${escapeHtml(a.status)}</span>
          </div>
          <div class="item-details">${escapeHtml(a.details)}</div>
          <div class="item-time">Recorded: ${escapeHtml(a.created_at || "")}</div>
        </div>
      `).join("");
    }

    // Escalations list
    if (escalations.length === 0) {
      escalationsList.innerHTML = `<div class="empty-state">No escalations created yet.</div>`;
    } else {
      escalationsList.innerHTML = escalations.map(e => `
        <div class="item-card" style="border-left: 3px solid #f59e0b;">
          <div class="item-header">
            <strong>${escapeHtml(e.category)}</strong>
            <span class="item-badge status-${e.status}">${escapeHtml(e.status)}</span>
          </div>
          <div class="item-details">${escapeHtml(e.reason)}</div>
          <div class="item-time">${escapeHtml(e.created_at || "")}</div>
        </div>
      `).join("");
    }
  }

  // Update Telemetry Box
  function updateTelemetry(data) {
    telProvider.textContent = data.provider_used || "local";
    telModel.textContent = data.model_used || "deterministic-engine";
    telIntent.textContent = data.intent || "--";
    telEmotion.textContent = data.emotion || "neutral";
    telDecision.textContent = data.decision || "--";
    telRationale.textContent = data.reason || "Policy rules checked successfully.";

    if (data.policies_cited && data.policies_cited.length > 0) {
      telPolicies.innerHTML = data.policies_cited.map(p => `<span class="policy-badge">${escapeHtml(p)}</span>`).join("");
    } else {
      telPolicies.innerHTML = `<span style="color: var(--text-dim);">None</span>`;
    }
  }

  // Load Policies Knowledge Base
  async function loadPolicies() {
    try {
      const res = await fetch("/api/policies");
      const policies = await res.json();
      policiesList.innerHTML = policies.map(p => `
        <div class="item-card">
          <div class="item-header">
            <span class="policy-badge">${escapeHtml(p.code)}</span>
            <span style="font-size:11px; color: var(--text-muted);">${escapeHtml(p.category)}</span>
          </div>
          <div style="font-weight:700; margin: 4px 0;">${escapeHtml(p.title)}</div>
          <div class="item-details">${escapeHtml(p.rule_text)}</div>
          <div style="font-size: 10px; color: var(--primary); margin-top:4px;">${escapeHtml(p.citation)}</div>
        </div>
      `).join("");
    } catch (e) {
      console.error("Error loading policies:", e);
    }
  }

  // System Health Status
  async function checkSystemStatus() {
    try {
      const res = await fetch("/api/system/status");
      const data = await res.json();
      aiProviderText.textContent = `AI: ${data.provider.toUpperCase()} (${data.model})`;
      if (data.provider_status === "ready" || data.status === "operational") {
        aiStatusPill.className = "status-pill status-ready";
      }
    } catch (e) {
      aiProviderText.textContent = "AI: Offline Mode";
    }
  }

  // Fetch Customers on startup
  async function init() {
    try {
      const res = await fetch("/api/customers");
      const custs = await res.json();
      custs.forEach(c => { customersData[c.id] = c; });
      renderProfileAndFlight(currentCustomerKey);
      await loadConversation(currentCustomerKey);
      await loadPolicies();
      await checkSystemStatus();
    } catch (err) {
      console.error("Initialization error:", err);
    }
  }

  function scrollChatToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[c]));
  }

  init();
});
