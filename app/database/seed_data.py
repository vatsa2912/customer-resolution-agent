import json
from app.database.connection import get_db_connection

def seed_initial_data(db_path=None):
    conn = get_db_connection(db_path)
    with conn:
        # Check if already seeded
        cursor = conn.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] > 0:
            return

        # 1. Customers from Assignment 3 PDF
        customers = [
            (
                "priya",
                "Priya Nair",
                "Gold",
                "SK4821X",
                "priya.nair@example.com",
                "+91-98xxxxxxx1",
                "6 flights, 1 prior complaint (delayed baggage, resolved with voucher)"
            ),
            (
                "arvind",
                "Arvind Kulkarni",
                "Silver",
                "TR1190B",
                "arvind.kulkarni@example.com",
                "+91-98xxxxxxx2",
                "3 flights, no prior complaints"
            ),
            (
                "meher",
                "Meher Kaur",
                "Platinum",
                "WL7742",
                "meher.kaur@example.com",
                "+91-98xxxxxxx3",
                "10 flights, 1 prior complaint (overbooking, resolved with a tier-status upgrade)"
            )
        ]
        conn.executemany(
            "INSERT OR REPLACE INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)",
            customers
        )

        # 2. Bookings
        bookings = [
            ("SK4821X", "priya", "Active - Disrupted"),
            ("TR1190B", "arvind", "Active - Delayed"),
            ("WL7742", "meher", "Active - Delayed")
        ]
        conn.executemany(
            "INSERT OR REPLACE INTO bookings VALUES (?, ?, ?)",
            bookings
        )

        # 3. Flights
        flights = [
            (
                "SK-204",
                "SK4821X",
                "Delhi → Goa",
                "Wed 23 Sep 2026",
                "18:40",
                None,
                "Cancelled (operational reasons)",
                "operational reasons",
                0.0,
                0
            ),
            (
                "Return",
                "SK4821X",
                "Goa → Delhi",
                "Fri 25 Sep 2026",
                "16:20",
                None,
                "Unaffected",
                "",
                0.0,
                1
            ),
            (
                "SK-118",
                "TR1190B",
                "Mumbai → Bengaluru",
                "Wed 23 Sep 2026",
                "07:10",
                "11:10",
                "Delayed 4h (new departure 11:10)",
                "Weather/ATC operational delay",
                4.0,
                0
            ),
            (
                "SK-305",
                "WL7742",
                "Delhi → Hyderabad",
                "Wed 23 Sep 2026",
                "14:00",
                "20:00",
                "Delayed 6h (new departure 20:00)",
                "Technical delay",
                6.0,
                0
            )
        ]
        conn.executemany(
            """INSERT INTO flights (
                flight_number, booking_pnr, route, date, scheduled_departure,
                new_departure, status, reason, delay_hours, is_return
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            flights
        )

        # 4. Service Policies from Assignment 3 PDF
        policies = [
            (
                "POL-CANCEL-01",
                "cancellation",
                "Cancellation Rebooking / Full Refund Rule",
                "If a flight is cancelled by the airline, the customer is entitled to a free rebooking on the next available flight within 24 hours, or a full refund, customer's choice.",
                json.dumps({
                    "entitlement": ["free_rebooking_24h", "full_refund"],
                    "free_rebooking_window_hours": 24,
                    "condition": "airline_caused_cancellation"
                })
            ),
            (
                "POL-DELAY-01",
                "delay",
                "Delay Compensation: Under 3 Hours",
                "Delay under 3 hours: ₹500 meal voucher.",
                json.dumps({
                    "min_hours": 0.0,
                    "max_hours": 3.0,
                    "benefits": ["₹500 meal voucher"]
                })
            ),
            (
                "POL-DELAY-02",
                "delay",
                "Delay Compensation: More Than 3 Hours",
                "Delay more than 3 hours: meal voucher + lounge access.",
                json.dumps({
                    "min_hours": 3.0,
                    "max_hours": 5.0,
                    "benefits": ["meal voucher", "lounge access"]
                })
            ),
            (
                "POL-DELAY-03",
                "delay",
                "Delay Compensation: More Than 5 Hours",
                "Delay more than 5 hours: meal voucher + hotel accommodation, covering only the delayed hours (not a full night's stay).",
                json.dumps({
                    "min_hours": 5.0,
                    "benefits": ["meal voucher", "hotel accommodation (delayed hours only)"],
                    "hotel_limitation": "covering only delayed hours, not full night"
                })
            ),
            (
                "POL-REFUND-01",
                "refund",
                "Refund Processing Rule",
                "Refunds for airline-caused cancellations are processed in full within 7 business days. Refunds are issued to the original payment method only.",
                json.dumps({
                    "processing_days": 7,
                    "payment_method": "original_payment_method_only",
                    "exception_requires_supervisor": True
                })
            ),
            (
                "POL-FARE-01",
                "fare",
                "Fare Difference Rule",
                "If a customer voluntarily chooses to rebook on a higher-fare flight (not airline-caused), they must pay the fare difference. Agents cannot waive fare differences above ₹1,500 without supervisor approval.",
                json.dumps({
                    "max_agent_waiver": 1500,
                    "requires_supervisor_approval_above": 1500
                })
            ),
            (
                "POL-LOYALTY-01",
                "loyalty",
                "Loyalty Tier Rule",
                "Gold and Platinum tier customers get priority rebooking (first access to next-available seats) but no additional compensation beyond the standard policy.",
                json.dumps({
                    "priority_rebooking_tiers": ["Gold", "Platinum"],
                    "extra_compensation_allowed": False
                })
            ),
            (
                "POL-PROHIBIT-01",
                "escalation",
                "Prohibited Actions & Mandatory Human Escalation",
                "Must escalate to a human agent: Approving compensation beyond policy; Waiving fare difference above ₹1,500; Non-airline disruptions; Legal action threats or formal complaints; Refunds to different payment methods.",
                json.dumps({
                    "prohibited_actions": [
                        "unauthorized_compensation",
                        "waive_fare_above_1500",
                        "non_airline_exception",
                        "legal_threat",
                        "formal_complaint",
                        "non_original_refund"
                    ]
                })
            )
        ]
        conn.executemany(
            "INSERT OR REPLACE INTO policies VALUES (?, ?, ?, ?, ?)",
            policies
        )

    conn.close()
