CUSTOMERS = {
    "priya": {
        "name": "Priya Nair",
        "tier": "Gold",
        "pnr": "SK4821X",
        "email": "priya.nair@example.com",
        "phone": "+91-98xxxxxxx1",
        "travel_history": "6 flights, 1 prior complaint: delayed baggage, resolved with voucher",
        "flights": [
            {
                "flight": "SK-204",
                "route": "Delhi → Goa",
                "date": "Wed 23 Sep 2026",
                "departure": "18:40",
                "status": "Cancelled",
                "reason": "operational reasons",
                "return": False,
            },
            {
                "flight": "Return flight",
                "route": "Goa → Delhi",
                "date": "Fri 25 Sep 2026",
                "departure": "16:20",
                "status": "Unaffected",
                "reason": "",
                "return": True,
            },
        ],
    },
    "arvind": {
        "name": "Arvind Kulkarni",
        "tier": "Silver",
        "pnr": "TR1190B",
        "email": "arvind.kulkarni@example.com",
        "phone": "+91-98xxxxxxx2",
        "travel_history": "3 flights, no prior complaints",
        "flights": [
            {
                "flight": "SK-118",
                "route": "Mumbai → Bengaluru",
                "date": "Wed 23 Sep 2026",
                "departure": "11:10",
                "original_departure": "07:10",
                "status": "Delayed 4h",
                "reason": "",
                "return": False,
            }
        ],
    },
    "meher": {
        "name": "Meher Kaur",
        "tier": "Platinum",
        "pnr": "WL7742",
        "email": "meher.kaur@example.com",
        "phone": "+91-98xxxxxxx3",
        "travel_history": "10 flights, 1 prior complaint: overbooking, resolved with tier-status upgrade",
        "flights": [
            {
                "flight": "SK-305",
                "route": "Delhi → Hyderabad",
                "date": "Wed 23 Sep 2026",
                "departure": "20:00",
                "original_departure": "14:00",
                "status": "Delayed 6h",
                "reason": "",
                "return": False,
            }
        ],
    },
}

POLICIES = {
    "cancellation": "For an airline-caused cancellation, the customer may choose free rebooking on the next available flight within 24 hours or a full refund.",
    "delay_under_3": "Delay under 3 hours: ₹500 meal voucher.",
    "delay_over_3": "Delay more than 3 hours: meal voucher + lounge access.",
    "delay_over_5": "Delay more than 5 hours: meal voucher + hotel accommodation covering only the delayed hours, not a full night.",
    "refund": "Airline-caused cancellation refunds are processed in full within 7 business days to the original payment method only.",
    "fare_difference": "A customer choosing a higher-fare flight voluntarily must pay the fare difference. Agents cannot waive fare differences above ₹1,500 without supervisor approval.",
    "loyalty": "Gold and Platinum customers receive priority rebooking, but no additional compensation beyond standard policy.",
}
