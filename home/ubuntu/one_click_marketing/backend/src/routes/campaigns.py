# backend/src/routes/campaigns.py

from flask import Blueprint, request, jsonify
from ..models.user import User, ClientProfile, db
from ..models.campaign import Campaign
from ..models.message_template import MessageTemplate
from ..models.message_log import MessageLog # For logging messages sent as part of a campaign
from ..services.whatsapp_service import WhatsAppService # To send messages
from ..routes.meta_integration import token_required
import logging
import json
from datetime import datetime
import time # For potential delays in a loop

logger = logging.getLogger(__name__)

campaigns_bp = Blueprint("campaigns_bp", __name__, url_prefix="/api/v1/campaigns")

@campaigns_bp.route("", methods=["POST"])
@token_required
def create_campaign():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    client_id = request.current_user_id
    campaign_name = data.get("campaign_name")
    template_id = data.get("template_id")
    audience_json = data.get("audience_json") # Expecting a JSON string of a list of phone numbers
    personalization_data_json = data.get("personalization_data_json") # JSON string: {"phone": {"var_name": "val"}}
    scheduled_at_str = data.get("scheduled_at") # ISO format string or null

    if not campaign_name or not template_id or not audience_json:
        return jsonify({"message": "Missing required fields: campaign_name, template_id, audience_json"}), 400

    template = MessageTemplate.query.filter_by(id=template_id, client_id=client_id).first()
    if not template:
        return jsonify({"message": "Message template not found or access denied."}), 404
    if template.status != "APPROVED_BY_META":
        return jsonify({"message": f"Template 	{template.template_name}	 is not approved by Meta. Current status: {template.status}"}), 400

    scheduled_at = None
    if scheduled_at_str:
        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str.replace("Z", "+00:00"))
        except ValueError:
            return jsonify({"message": "Invalid scheduled_at format. Use ISO 8601 format."}), 400

    try:
        audience_list = json.loads(audience_json)
        if not isinstance(audience_list, list):
            raise ValueError("Audience JSON must be a list of phone numbers.")
        total_recipients = len(audience_list)
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({"message": f"Invalid audience_json: {str(e)}"}), 400
    
    parsed_personalization_data = {}
    if personalization_data_json:
        try:
            parsed_personalization_data = json.loads(personalization_data_json)
            if not isinstance(parsed_personalization_data, dict):
                raise ValueError("Personalization data JSON must be an object.")
        except (json.JSONDecodeError, ValueError) as e:
            return jsonify({"message": f"Invalid personalization_data_json: {str(e)}"}), 400

    try:
        new_campaign = Campaign(
            client_id=client_id,
            template_id=template_id,
            campaign_name=campaign_name,
            audience_json=audience_json, # Store the original JSON
            personalization_data_json=personalization_data_json, # Store the original JSON
            scheduled_at=scheduled_at,
            status="DRAFT",
            total_recipients=total_recipients
        )
        if scheduled_at and scheduled_at > datetime.utcnow():
            new_campaign.status = "SCHEDULED"
        elif not scheduled_at:
             new_campaign.status = "PENDING_SEND" # Ready for manual trigger
        
        db.session.add(new_campaign)
        db.session.commit()
        logger.info(f"New campaign 	{campaign_name}	 created for client ID {client_id}, Campaign ID {new_campaign.id}")
        return jsonify({
            "message": "Campaign created successfully.", 
            "campaign_id": new_campaign.id,
            "campaign_name": new_campaign.campaign_name,
            "status": new_campaign.status
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating campaign: {str(e)}", exc_info=True)
        return jsonify({"message": "Failed to create campaign", "error": str(e)}), 500

@campaigns_bp.route("", methods=["GET"])
@token_required
def get_campaigns():
    client_id = request.current_user_id
    try:
        campaigns = Campaign.query.filter_by(client_id=client_id).order_by(Campaign.created_at.desc()).all()
        results = []
        for camp in campaigns:
            results.append({
                "id": camp.id,
                "campaign_name": camp.campaign_name,
                "template_id": camp.template_id,
                "template_name": camp.template.template_name if camp.template else None,
                "status": camp.status,
                "scheduled_at": camp.scheduled_at.isoformat() if camp.scheduled_at else None,
                "total_recipients": camp.total_recipients,
                "messages_sent_count": camp.messages_sent_count,
                "created_at": camp.created_at.isoformat(),
                "updated_at": camp.updated_at.isoformat()
            })
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error fetching campaigns for client {client_id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Failed to retrieve campaigns", "error": str(e)}), 500

@campaigns_bp.route("/<int:campaign_id>", methods=["GET"])
@token_required
def get_campaign(campaign_id):
    client_id = request.current_user_id
    try:
        camp = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
        if not camp:
            return jsonify({"message": "Campaign not found or access denied"}), 404
        
        return jsonify({
            "id": camp.id,
            "campaign_name": camp.campaign_name,
            "template_id": camp.template_id,
            "template_name": camp.template.template_name if camp.template else None,
            "audience_json": camp.audience_json,
            "personalization_data_json": camp.personalization_data_json,
            "status": camp.status,
            "scheduled_at": camp.scheduled_at.isoformat() if camp.scheduled_at else None,
            "actual_sent_at": camp.actual_sent_at.isoformat() if camp.actual_sent_at else None,
            "total_recipients": camp.total_recipients,
            "messages_sent_count": camp.messages_sent_count,
            "messages_delivered_count": camp.messages_delivered_count,
            "messages_read_count": camp.messages_read_count,
            "messages_failed_count": camp.messages_failed_count,
            "created_at": camp.created_at.isoformat(),
            "updated_at": camp.updated_at.isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error fetching campaign {campaign_id} for client {client_id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Failed to retrieve campaign", "error": str(e)}), 500

@campaigns_bp.route("/<int:campaign_id>", methods=["PUT"])
@token_required
def update_campaign(campaign_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    client_id = request.current_user_id
    camp = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
    if not camp:
        return jsonify({"message": "Campaign not found or access denied"}), 404
    
    if camp.status not in ["DRAFT", "SCHEDULED", "PENDING_SEND"]:
        return jsonify({"message": f"Campaign cannot be updated in its current status: {camp.status}"}), 400

    try:
        if "campaign_name" in data: camp.campaign_name = data["campaign_name"]
        if "template_id" in data: 
            template = MessageTemplate.query.filter_by(id=data["template_id"], client_id=client_id).first()
            if not template: return jsonify({"message": "Template not found"}), 404
            if template.status != "APPROVED_BY_META": return jsonify({"message": "Template not approved by Meta"}), 400
            camp.template_id = data["template_id"]
        if "audience_json" in data: 
            camp.audience_json = data["audience_json"]
            try:
                audience_list = json.loads(data["audience_json"])
                camp.total_recipients = len(audience_list)
            except: return jsonify({"message": "Invalid audience_json"}),400
        if "personalization_data_json" in data: camp.personalization_data_json = data["personalization_data_json"]
        if "scheduled_at" in data:
            scheduled_at_str = data.get("scheduled_at")
            if scheduled_at_str:
                camp.scheduled_at = datetime.fromisoformat(scheduled_at_str.replace("Z", "+00:00"))
                camp.status = "SCHEDULED" if camp.scheduled_at > datetime.utcnow() else camp.status
            else:
                camp.scheduled_at = None
                camp.status = "PENDING_SEND" if camp.status == "SCHEDULED" else camp.status
        
        db.session.commit()
        logger.info(f"Campaign ID {campaign_id} updated for client ID {client_id}")
        return jsonify({"message": "Campaign updated successfully.", "campaign_id": camp.id, "status": camp.status}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating campaign {campaign_id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Failed to update campaign", "error": str(e)}), 500

@campaigns_bp.route("/<int:campaign_id>", methods=["DELETE"])
@token_required
def delete_campaign(campaign_id):
    client_id = request.current_user_id
    camp = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
    if not camp:
        return jsonify({"message": "Campaign not found or access denied"}), 404

    if camp.status not in ["DRAFT", "SCHEDULED", "CANCELLED", "FAILED", "COMPLETED", "PENDING_SEND"]:
         return jsonify({"message": f"Campaign cannot be deleted in its current status: {camp.status}. You might need to cancel it first."}), 400

    try:
        db.session.delete(camp)
        db.session.commit()
        logger.info(f"Campaign ID {campaign_id} deleted for client ID {client_id}")
        return jsonify({"message": "Campaign deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting campaign {campaign_id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Failed to delete campaign", "error": str(e)}), 500

@campaigns_bp.route("/<int:campaign_id>/send", methods=["POST"])
@token_required
def send_campaign_now(campaign_id):
    client_id = request.current_user_id
    client_profile = request.current_client_profile # from token_required decorator

    camp = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
    if not camp:
        return jsonify({"message": "Campaign not found or access denied"}), 404

    if camp.status not in ["PENDING_SEND", "DRAFT", "SCHEDULED"]: # Allow sending scheduled ones manually too
        return jsonify({"message": f"Campaign cannot be sent in its current status: {camp.status}"}), 400

    if not client_profile.meta_access_token_encrypted or not client_profile.meta_phone_number_id:
        return jsonify({"message": "Meta API credentials not configured for this client."}), 400

    template = camp.template
    if not template or template.status != "APPROVED_BY_META":
        camp.status = "FAILED"
        camp.failure_reason = "Template not found or not approved by Meta."
        db.session.commit()
        return jsonify({"message": camp.failure_reason}), 400

    try:
        audience_list = json.loads(camp.audience_json)
        personalization_map = json.loads(camp.personalization_data_json or "{}")
        variables_expected = json.loads(template.variables_expected_json or "[]")
    except Exception as e:
        camp.status = "FAILED"
        camp.failure_reason = f"Error parsing campaign data (audience, personalization, or template variables): {str(e)}"
        db.session.commit()
        return jsonify({"message": camp.failure_reason}), 400

    camp.status = "SENDING"
    camp.actual_sent_at = datetime.utcnow()
    db.session.commit()

    whatsapp_service = WhatsAppService(
        access_token=client_profile.meta_access_token_encrypted, 
        phone_number_id=client_profile.meta_phone_number_id
    )

    sent_count = 0
    failed_count = 0

    for recipient_phone in audience_list:
        components = []
        recipient_personalization = personalization_map.get(str(recipient_phone), {}) # Ensure phone is string key
        
        # Assuming template_structure_json helps identify where variables go (header, body)
        # For simplicity, let's assume all variables go into the body for now if not specified further.
        # A more robust solution would parse template_structure_json to build components for header, body, buttons.
        
        body_params = []
        # If variables_expected_json is an ordered list of keys for {{1}}, {{2}}...
        if variables_expected:
            for var_key in variables_expected:
                body_params.append({
                    "type": "text",
                    "text": str(recipient_personalization.get(var_key, "")) # Default to empty string if var not found
                })
        
        if body_params:
            components.append({"type": "body", "parameters": body_params})
        
        # TODO: Add support for header variables and button payload variables based on template_structure_json

        log_entry = MessageLog(
            client_id=client_id,
            campaign_id=camp.id,
            recipient_phone_number=recipient_phone,
            sender_phone_number_id=client_profile.meta_phone_number_id,
            message_type="template",
            direction="outgoing",
            template_name=template.template_name,
            message_content_rendered=f"Personalized template {template.template_name} to {recipient_phone} with vars: {recipient_personalization}",
            status="pending_api_call"
        )
        db.session.add(log_entry)
        db.session.commit() # Get ID for log_entry

        try:
            api_response = whatsapp_service.send_template_message(
                recipient_phone_number=recipient_phone,
                template_name=template.template_name,
                language_code=template.language_code,
                components=components if components else None
            )

            if api_response and "error" not in api_response and api_response.get("messages"):
                log_entry.whatsapp_message_id = api_response.get("messages", [{}])[0].get("id")
                log_entry.status = "sent_to_whatsapp" # Will be updated by webhook later
                sent_count += 1
            else:
                log_entry.status = "failed_on_send"
                error_details = api_response.get("error", {}) if api_response else {}
                log_entry.failure_reason = error_details.get("message", str(api_response.get("details", "Unknown API error")))
                failed_count += 1
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e_send:
            logger.error(f"Exception sending message to {recipient_phone} in campaign {camp.id}: {str(e_send)}")
            log_entry.status = "failed_internal_error_on_send"
            log_entry.failure_reason = str(e_send)
            failed_count += 1
            db.session.add(log_entry)
            db.session.commit()
        
        # Optional: add a small delay to avoid hitting rate limits too hard in a simple loop
        # time.sleep(0.1) # 100ms

    camp.messages_sent_count = sent_count
    camp.messages_failed_count = failed_count # Initial failed count, webhooks might update this
    camp.status = "COMPLETED" if failed_count == 0 else "PARTIALLY_COMPLETED"
    if sent_count == 0 and failed_count > 0:
        camp.status = "FAILED"
        
    db.session.commit()

    logger.info(f"Campaign {camp.id} processing finished. Sent: {sent_count}, Failed: {failed_count}")
    return jsonify({
        "message": f"Campaign processing finished. Sent: {sent_count}, Failed: {failed_count}",
        "campaign_id": camp.id,
        "status": camp.status
    }), 200

# Remember to register this blueprint in main.py

