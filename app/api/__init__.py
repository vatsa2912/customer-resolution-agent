from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

from app.api import chat_routes, customer_routes, action_routes, escalation_routes, system_routes

__all__ = ["api_bp"]
