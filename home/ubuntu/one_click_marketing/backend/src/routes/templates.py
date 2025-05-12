# backend/src/routes/templates.py

from flask import Blueprint, request, jsonify
from ..models.user import User, ClientProfile, db
from ..models.message_template import MessageTemplate
from ..routes.meta_integration import token_required # Re-use the token_required decorator
import logging

logger = logging.getLogger(__name__)

templates_bp = Blueprint("templates_bp", __name__, url_prefix="/api/v1/templates")

@templates_bp.route("", methods=["POST"])
@token_required
def create_template():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    client_id = request.current_user_id
    template_name = data.get("template_name")
    category = data.get("category")
    language_code = data.get("language_code", "en_US")
    template_structure_json = data.get("template_structure_json") # Should be a JSON string
    variables_expected_json = data.get("variables_expected_json") # Should be a JSON string
    status = data.get("status", "DRAFT") # Default to DRAFT, can be PENDING_META_APPROVAL

    if not template_name or not category or not template_structure_json:
        return jsonify({"message": "Missing required fields: template_name, category, template_structure_json"}), 400

    # Basic validation for template_name uniqueness per client could be added here if needed
    # existing_template = MessageTemplate.query.filter_by(client_id=client_id, template_name=template_name).first()
    # if existing_template:
    #     return jsonify({"message": f"Template with name 	{template_name}	 already exists for this client."}), 409

    try:
        new_template = MessageTemplate(
            client_id=client_id,
            template_name=template_name,
            category=category,
            language_code=language_code,
            template_structure_json=template_structure_json,
            variables_expected_json=variables_expected_json,
            status=status
        )
        db.session.add(new_template)
        db.session.commit()
        logger.info(f"New template 	{template_name}	 created for client ID {client_id}")
        return jsonify({
            "message": "Message template created successfully.", 
            "template_id": new_template.id,
            "template_name": new_template.template_name
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating message template: {str(e)}")
        return jsonify({"message": "Failed to create message template", "error": str(e)}), 500

@templates_bp.route("", methods=["GET"])
@token_required
def get_templates():
    client_id = request.current_user_id
    try:
        templates = MessageTemplate.query.filter_by(client_id=client_id).order_by(MessageTemplate.updated_at.desc()).all()
        results = []
        for tpl in templates:
            results.append({
                "id": tpl.id,
                "client_id": tpl.client_id,
                "template_name": tpl.template_name,
                "category": tpl.category,
                "language_code": tpl.language_code,
                "template_structure_json": tpl.template_structure_json,
                "variables_expected_json": tpl.variables_expected_json,
                "status": tpl.status,
                "meta_rejection_reason": tpl.meta_rejection_reason,
                "created_at": tpl.created_at.isoformat(),
                "updated_at": tpl.updated_at.isoformat()
            })
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error fetching templates for client {client_id}: {str(e)}")
        return jsonify({"message": "Failed to retrieve templates", "error": str(e)}), 500

@templates_bp.route("/<int:template_id>", methods=["GET"])
@token_required
def get_template(template_id):
    client_id = request.current_user_id
    try:
        tpl = MessageTemplate.query.filter_by(id=template_id, client_id=client_id).first()
        if not tpl:
            return jsonify({"message": "Template not found or access denied"}), 404
        
        return jsonify({
            "id": tpl.id,
            "client_id": tpl.client_id,
            "template_name": tpl.template_name,
            "category": tpl.category,
            "language_code": tpl.language_code,
            "template_structure_json": tpl.template_structure_json,
            "variables_expected_json": tpl.variables_expected_json,
            "status": tpl.status,
            "meta_rejection_reason": tpl.meta_rejection_reason,
            "created_at": tpl.created_at.isoformat(),
            "updated_at": tpl.updated_at.isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error fetching template {template_id} for client {client_id}: {str(e)}")
        return jsonify({"message": "Failed to retrieve template", "error": str(e)}), 500

@templates_bp.route("/<int:template_id>", methods=["PUT"])
@token_required
def update_template(template_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    client_id = request.current_user_id
    tpl = MessageTemplate.query.filter_by(id=template_id, client_id=client_id).first()
    if not tpl:
        return jsonify({"message": "Template not found or access denied"}), 404

    try:
        # Update fields if they are provided in the request
        if "template_name" in data: tpl.template_name = data["template_name"]
        if "category" in data: tpl.category = data["category"]
        if "language_code" in data: tpl.language_code = data["language_code"]
        if "template_structure_json" in data: tpl.template_structure_json = data["template_structure_json"]
        if "variables_expected_json" in data: tpl.variables_expected_json = data["variables_expected_json"]
        if "status" in data: tpl.status = data["status"]
        if "meta_rejection_reason" in data: tpl.meta_rejection_reason = data["meta_rejection_reason"]
        
        db.session.commit()
        logger.info(f"Template ID {template_id} updated for client ID {client_id}")
        return jsonify({"message": "Message template updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating template {template_id}: {str(e)}")
        return jsonify({"message": "Failed to update message template", "error": str(e)}), 500

@templates_bp.route("/<int:template_id>", methods=["DELETE"])
@token_required
def delete_template(template_id):
    client_id = request.current_user_id
    tpl = MessageTemplate.query.filter_by(id=template_id, client_id=client_id).first()
    if not tpl:
        return jsonify({"message": "Template not found or access denied"}), 404

    try:
        db.session.delete(tpl)
        db.session.commit()
        logger.info(f"Template ID {template_id} deleted for client ID {client_id}")
        return jsonify({"message": "Message template deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting template {template_id}: {str(e)}")
        return jsonify({"message": "Failed to delete message template", "error": str(e)}), 500

# Remember to register this blueprint in your main Flask app (e.g., main.py)
# from .routes.templates import templates_bp
# app.register_blueprint(templates_bp)

