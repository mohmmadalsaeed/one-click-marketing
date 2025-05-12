# backend/src/routes/admin_pricing.py

from flask import Blueprint, request, jsonify
from ..models.user import db, User
from ..models.client_pricing import ClientPricing
from ..routes.meta_integration import token_required # Re-use token_required for admin routes
from ..services.admin_service import AdminService # Assuming an AdminService for role checks
import decimal
import logging

logger = logging.getLogger(__name__)

admin_pricing_bp = Blueprint("admin_pricing_bp", __name__, url_prefix="/api/v1/admin/pricing")

# Helper to check if user is admin
# This might be part of a more generic AdminService or decorator
def admin_required(fn):
    @token_required
    def wrapper(*args, **kwargs):
        current_user_id = request.current_user_id
        user = User.query.get(current_user_id)
        if not user or user.role != "admin":
            return jsonify({"message": "Admin access required"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__ # Preserve original function name for Flask
    return wrapper

@admin_pricing_bp.route("/client/<int:client_id>", methods=["POST", "PUT"])
@admin_required
def set_client_pricing(client_id):
    data = request.get_json()
    if not data or "price_per_message" not in data:
        return jsonify({"message": "Missing price_per_message in request body"}), 400

    try:
        price_per_message = decimal.Decimal(str(data["price_per_message"]))
        if price_per_message < decimal.Decimal("0"): # Price cannot be negative
            return jsonify({"message": "price_per_message cannot be negative"}), 400
    except (decimal.InvalidOperation, ValueError):
        return jsonify({"message": "Invalid format for price_per_message"}), 400

    currency = data.get("currency", "USD") # Default to USD if not provided
    notes = data.get("notes")

    target_client = User.query.filter_by(id=client_id, role="client").first()
    if not target_client:
        return jsonify({"message": "Client not found or user is not a client"}), 404

    pricing = ClientPricing.query.filter_by(client_id=client_id).first()
    if request.method == "POST" and pricing:
        return jsonify({"message": "Pricing already exists for this client. Use PUT to update."}), 409 # Conflict
    
    if not pricing:
        pricing = ClientPricing(client_id=client_id)
        db.session.add(pricing)
    
    pricing.price_per_message = price_per_message
    pricing.currency = currency
    pricing.notes = notes

    try:
        db.session.commit()
        return jsonify({
            "message": "Client pricing set successfully",
            "client_id": pricing.client_id,
            "price_per_message": str(pricing.price_per_message),
            "currency": pricing.currency,
            "notes": pricing.notes
        }), 200 if request.method == "PUT" else 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting client pricing for client {client_id}: {str(e)}")
        return jsonify({"message": "Failed to set client pricing"}), 500

@admin_pricing_bp.route("/client/<int:client_id>", methods=["GET"])
@admin_required
def get_client_pricing(client_id):
    pricing = ClientPricing.query.filter_by(client_id=client_id).first()
    if not pricing:
        # Optionally, return a default pricing or indicate no specific pricing is set
        # For now, let's return 404 if no specific pricing is found
        return jsonify({"message": "No specific pricing found for this client."}), 404
    
    return jsonify({
        "client_id": pricing.client_id,
        "price_per_message": str(pricing.price_per_message),
        "currency": pricing.currency,
        "notes": pricing.notes,
        "updated_at": pricing.updated_at.isoformat()
    }), 200

@admin_pricing_bp.route("/client/<int:client_id>", methods=["DELETE"])
@admin_required
def delete_client_pricing(client_id):
    pricing = ClientPricing.query.filter_by(client_id=client_id).first()
    if not pricing:
        return jsonify({"message": "No specific pricing found for this client to delete."}), 404
    
    try:
        db.session.delete(pricing)
        db.session.commit()
        return jsonify({"message": "Client pricing deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting client pricing for client {client_id}: {str(e)}")
        return jsonify({"message": "Failed to delete client pricing"}), 500

@admin_pricing_bp.route("/clients", methods=["GET"])
@admin_required
def list_all_client_pricing():
    all_pricing = ClientPricing.query.join(User, ClientPricing.client_id == User.id)\
                                     .add_columns(User.username, User.email, ClientPricing.id, ClientPricing.client_id, ClientPricing.price_per_message, ClientPricing.currency, ClientPricing.notes, ClientPricing.updated_at)\
                                     .all()
    
    result = [
        {
            "pricing_id": p.id,
            "client_id": p.client_id,
            "username": p.username,
            "email": p.email,
            "price_per_message": str(p.price_per_message),
            "currency": p.currency,
            "notes": p.notes,
            "updated_at": p.updated_at.isoformat()
        } for p in all_pricing
    ]
    return jsonify(result), 200

# Remember to register this blueprint in your main Flask app (e.g., main.py)
# from .routes.admin_pricing import admin_pricing_bp
# app.register_blueprint(admin_pricing_bp)

