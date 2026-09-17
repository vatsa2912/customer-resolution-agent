from typing import Dict, Any, Optional
from app.database.repositories import CustomerRepository
from app.tools.registry import default_tool_registry

cust_repo = CustomerRepository()

@default_tool_registry.register(
    name="get_customer_profile",
    description="Retrieve the customer profile, loyalty tier, contact, and flight booking details.",
    parameters={
        "type": "object",
        "properties": {
            "customer_key": {"type": "string", "description": "Customer identifier (priya, arvind, meher)"}
        },
        "required": ["customer_key"]
    }
)
def get_customer_profile(customer_key: str) -> Optional[Dict[str, Any]]:
    return cust_repo.get_by_key(customer_key)

@default_tool_registry.register(
    name="get_booking_details",
    description="Retrieve flight and itinerary status for a given PNR booking reference.",
    parameters={
        "type": "object",
        "properties": {
            "pnr": {"type": "string", "description": "Passenger Name Record (e.g., SK4821X, TR1190B, WL7742)"}
        },
        "required": ["pnr"]
    }
)
def get_booking_details(pnr: str) -> Optional[Dict[str, Any]]:
    for cust in cust_repo.get_all():
        if cust["pnr"].upper() == pnr.upper():
            return {
                "customer_name": cust["name"],
                "tier": cust["tier"],
                "pnr": cust["pnr"],
                "flights": cust["flights"]
            }
    return None

@default_tool_registry.register(
    name="get_flight_status",
    description="Retrieve live status and disruption reasons for a specific flight number.",
    parameters={
        "type": "object",
        "properties": {
            "flight_number": {"type": "string", "description": "Flight code (e.g., SK-204, SK-118, SK-305)"}
        },
        "required": ["flight_number"]
    }
)
def get_flight_status(flight_number: str) -> Optional[Dict[str, Any]]:
    fn = flight_number.upper().strip()
    for cust in cust_repo.get_all():
        for f in cust["flights"]:
            if f["flight_number"].upper() == fn:
                return {
                    "flight_number": f["flight_number"],
                    "route": f["route"],
                    "date": f["date"],
                    "scheduled_departure": f["scheduled_departure"],
                    "new_departure": f["new_departure"],
                    "status": f["status"],
                    "reason": f["reason"],
                    "delay_hours": f["delay_hours"]
                }
    return None
