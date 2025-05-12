# backend/src/routes/client_portal.py

from flask import Blueprint, request, jsonify
from ..models.user import db, User
from ..models.client_pricing import ClientPricing
from ..routes.meta_integration import token_required # For client authentication
import logging

logger = logging.getLogger(__name__)

client_portal_bp = Blueprint("client_portal_bp", __name__, url_prefix="/api/v1/client")

@client_portal_bp.route("/my-pricing", methods=["GET"])
@token_required
def get_my_pricing_details():
    client_id = request.current_user_id

    pricing = ClientPricing.query.filter_by(client_id=client_id).first()

    if not pricing:
        # If no specific pricing, you might return a system default or a specific message.
        # For now, let's indicate no specific pricing is set for this client.
        # The frontend can then display a generic message or a default rate if applicable.
        # Returning 404 might be too strong if there's a fallback default system price.
        # Let's return a specific structure indicating no custom pricing.
        # However, the frontend page expects a 404 to show "standard pricing" message.
        # So, let's stick to 404 if no ClientPricing record exists.
        return jsonify({"message": "No client-specific pricing configuration found."}), 404
    
    return jsonify({
        "price_per_message": str(pricing.price_per_message),
        "currency": pricing.currency,
        "notes": pricing.notes, # Admin notes, client frontend might not display this.
        "updated_at": pricing.updated_at.isoformat() if pricing.updated_at else None
    }), 200

# Remember to register this blueprint in your main Flask app (e.g., main.py)
# from .routes.client_portal import client_portal_bp
# app.register_blueprint(client_portal_bp)

