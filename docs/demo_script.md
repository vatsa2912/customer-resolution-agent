# AIONOS Reviewer Demo Script

This document provides exact, step-by-step instructions for testing and evaluating the AeroResolve AI Customer Support System across all Assignment 3 requirements.

---

## Quick Launch

1. In PowerShell, activate the virtual environment and launch the app:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   python app.py
   ```
2. Open your web browser to:
   ```text
   http://127.0.0.1:5000
   ```

---

## Scenario Walkthroughs

### 🎯 Scenario 1: Priya Nair (Gold Tier, PNR: SK4821X)

**Context**: Flight SK-204 (Delhi → Goa) is cancelled due to operational reasons. Priya is furious, demands a full refund, and wants a free upgrade to business class on her return flight.

1. In the left panel, select **Priya Nair — Gold Tier**.
2. Click the preset button: **Scenario 1: Priya: Cancelled + Angry + Business Upgrade** (or paste: `"I am furious. My flight was cancelled. I want a full cash refund plus a free upgrade to business class on my return flight."`).
3. Press **Send**.
4. **Observe the Agent's Response**:
   - **Empathy & Composure**: Acknowledges Priya's anger professionally without arguing or over-apologizing.
   - **Cancellation Cause**: Explains flight SK-204 was cancelled due to operational reasons.
   - **Policy Limitation**: Clearly states that under policy `POL-LOYALTY-01`, Gold tier members receive priority rebooking, but **complimentary business-class upgrades or extra compensation are not permitted**.
   - **Supervisor Escalation**: Informs her that her upgrade request has been escalated to a supervisor (`POL-PROHIBIT-01`). Check the **Escalations** tab on the right panel to see the live ticket.
   - **Action Proposal**: Explains full refund eligibility (processed to original payment method within 7 business days per `POL-REFUND-01`) or free 24-hour rebooking.
   - **Interactive Confirmation Card**: An action card appears in chat: `Full refund for flight SK-204`.
5. **Multi-Turn Confirmation Test**:
   - Type `"Yes, please proceed with the refund"` OR click the green **✓ Approve & Execute** button.
   - The agent executes the simulated refund and updates the action status to `executed`. Check the **Actions** tab on the right panel to view the completed record.

---

### 🎯 Scenario 2: Arvind Kulkarni (Silver Tier, PNR: TR1190B)

**Context**: Flight SK-118 (Mumbai → Bengaluru) is delayed 4 hours (new departure 11:10). Arvind is frustrated about missing a connecting meeting and demands hotel accommodation.

1. In the customer dropdown, select **Arvind Kulkarni — Silver Tier**.
2. Click the preset button: **Scenario 2: Arvind: 4h Delay + Hotel Request** (or paste: `"My flight is delayed by 4 hours. I missed an important meeting. I want hotel accommodation."`).
3. Press **Send**.
4. **Observe the Agent's Response**:
   - **Empathetic Acknowledgment**: Acknowledges the disruption to his business meeting.
   - **Correct Policy Application (`POL-DELAY-02`)**: Explains that a 4-hour delay qualifies for a complimentary **meal voucher + lounge access**.
   - **Strict Hotel Threshold**: Politely explains that under policy `POL-DELAY-03`, hotel accommodation is provided **only for delays exceeding 5 hours**.
   - **Action Execution**: Directly applies the meal voucher and lounge pass to his account. View the record under the **Actions** tab.

---

### 🎯 Scenario 3: Meher Kaur (Platinum Tier, PNR: WL7742)

**Context**: Flight SK-305 (Delhi → Hyderabad) is delayed 6 hours (new departure 20:00). Meher requests a full night's hotel stay (not just delayed hours), and asks to be moved onto a different, higher-fare flight with a ₹2,000 fare difference waived.

1. In the customer dropdown, select **Meher Kaur — Platinum Tier**.
2. Click the preset button: **Scenario 3: Meher: 6h Delay + Full Hotel + ₹2,000 Waiver** (or paste: `"My flight is delayed by 6 hours. I want a full night's hotel stay. Also move me to another higher-fare flight. The fare difference is ₹2,000. I want you to waive it."`).
3. Press **Send**.
4. **Observe the Agent's Response**:
   - **Separation of Issues**: Carefully separates the hotel issue from the fare waiver issue.
   - **Hotel Eligibility (`POL-DELAY-03`)**: Grants meal voucher, lounge access, and hotel accommodation **covering strictly the delayed hours** until new departure (20:00), firmly explaining that a *full night's stay* is not included.
   - **Fare Difference Rule (`POL-FARE-01`)**: Explains that agents cannot waive fare differences exceeding ₹1,500 without supervisor approval.
   - **Supervisor Escalation (`POL-PROHIBIT-01`)**: Because her waiver request is ₹2,000, the agent escalates the waiver request to a human supervisor.
   - Check the **Escalations** tab to see the ticket categorized as `fare_waiver_over_limit`.
   - Check the **Actions** tab to see the applied delay compensation package.

---

### ⚖️ Scenario 4 (Edge Case): Legal Action & Formal Complaint

1. Select any customer and type:
   `"This is completely unacceptable. I am going to file a formal complaint and take legal action over this."`
2. Press **Send**.
3. **Observe the Agent's Response**:
   - The agent does not argue or make defensive statements.
   - Recognizes mandatory immediate escalation trigger (`POL-PROHIBIT-01`).
   - Informs the passenger that the matter is immediately routed to the specialist support team.
   - Check the **Escalations** tab to inspect the `legal_threat` ticket.

---

## Inspector Panel Features

1. **Actions Tab**: Real-time list of all proposed, awaiting confirmation, and executed actions with timestamps and simulation tags.
2. **Escalations Tab**: Supervisor queue displaying all escalated tickets with reasons and severity.
3. **Reasoning Tab**: Live telemetry displaying the active AI provider, extracted intent, detected customer emotion, decision status, and grounded policy citations.
4. **Policies Tab**: Complete reference of all 7 Assignment 3 service rules with verbatim policy text and citations.
