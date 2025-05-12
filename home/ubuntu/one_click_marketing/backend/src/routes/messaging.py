# backend/src/routes/messaging.py

from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from ..models.user import User, ClientProfile, db # Assuming db is accessible
from ..models.message_log import MessageLog # Import MessageLog model
from ..services.whatsapp_service import WhatsAppService
from ..routes.auth import SECRET_KEY # For token decoding to identify the user
from ..routes.meta_integration import token_required # Re-use the token_required decorator
import jwt # PyJWT library
import logging

logger = logging.getLogger(__name__)

messaging_bp = Blueprint("messaging_bp", __name__, url_prefix="/api/v1/messages")

@messaging_bp.route("/send-template", methods=["POST"])
@token_required # Ensures the user is authenticated and client_profile is available on request
def send_template_message_route():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    recipient_phone_number = data.get("recipient_phone_number")
    template_name = data.get("template_name")
    language_code = data.get("language_code", "en_US") # Default language code
    components = data.get("components") # Optional components for variables

    if not recipient_phone_number or not template_name:
        return jsonify({"message": "Missing recipient_phone_number or template_name"}), 400

    client_profile = request.current_client_profile

    if not client_profile.meta_access_token_encrypted or not client_profile.meta_phone_number_id:
        return jsonify({"message": "Meta API credentials not configured for this client."}), 400

    access_token = client_profile.meta_access_token_encrypted 
    phone_number_id = client_profile.meta_phone_number_id

    whatsapp_service = WhatsAppService(access_token=access_token, phone_number_id=phone_number_id)
    
    # Create a preliminary message log entry for outgoing message
    log_entry = MessageLog(
        client_id=client_profile.user_id,
        recipient_phone_number=recipient_phone_number,
        sender_phone_number_id=phone_number_id, # The app's sending number
        message_type="template",
        direction="outgoing",
        template_name=template_name,
        # Rendered content could be more complex to store, for now, just template name
        message_content_rendered=f"Template: {template_name} to {recipient_phone_number}", 
        status="pending" # Initial status
    )
    db.session.add(log_entry)
    try:
        db.session.commit() # Commit to get log_entry.id if needed, or commit after API call
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating initial MessageLog for outgoing template: {str(e)}")
        # Decide if we should still attempt to send or return error

    try:
        logger.info(f"Attempting to send template message 	{template_name}	 to {recipient_phone_number} for client ID {client_profile.user_id}")
        response = whatsapp_service.send_template_message(
            recipient_phone_number=recipient_phone_number,
            template_name=template_name,
            language_code=language_code,
            components=components
        )
        
        if response and "error" not in response and response.get("messages"):
            whatsapp_msg_id = response.get("messages", [{}])[0].get("id")
            log_entry.whatsapp_message_id = whatsapp_msg_id
            log_entry.status = "sent_to_whatsapp" # Or a status indicating it was accepted by WhatsApp API
            logger.info(f"Template message sent successfully via service. API Response: {response}")
            db.session.add(log_entry)
            db.session.commit()
            return jsonify({"message": "Template message sent successfully", "api_response": response, "log_id": log_entry.id}), 200
        else:
            log_entry.status = "failed_to_send"
            log_entry.failure_reason = response.get("error", {}).get("message") if response and response.get("error") else response.get("details", "Unknown error from WhatsApp service")
            db.session.add(log_entry)
            db.session.commit()
            logger.error(f"Failed to send template message via service. Error: {log_entry.failure_reason}")
            return jsonify({
                "message": "Failed to send template message", 
                "error_details": log_entry.failure_reason,
                "status_code_from_meta": response.get("status_code") if response else None
            }), response.get("status_code", 500) if response else 500

    except Exception as e:
        log_entry.status = "failed_internal_error"
        log_entry.failure_reason = str(e)
        db.session.add(log_entry)
        db.session.commit()
        logger.error(f"Exception in send_template_message_route: {str(e)}")
        return jsonify({"message": "An internal error occurred while sending the message", "error": str(e)}), 500

@messaging_bp.route("/send-text", methods=["POST"])
@token_required
def send_text_message_route():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    recipient_phone_number = data.get("recipient_phone_number")
    message_text = data.get("message_text")
    preview_url = data.get("preview_url", False)

    if not recipient_phone_number or not message_text:
        return jsonify({"message": "Missing recipient_phone_number or message_text"}), 400

    client_profile = request.current_client_profile

    if not client_profile.meta_access_token_encrypted or not client_profile.meta_phone_number_id:
        return jsonify({"message": "Meta API credentials not configured for this client."}), 400

    access_token = client_profile.meta_access_token_encrypted
    phone_number_id = client_profile.meta_phone_number_id

    whatsapp_service = WhatsAppService(access_token=access_token, phone_number_id=phone_number_id)
    
    log_entry = MessageLog(
        client_id=client_profile.user_id,
        recipient_phone_number=recipient_phone_number,
        sender_phone_number_id=phone_number_id,
        message_type="text",
        direction="outgoing",
        message_content_rendered=message_text,
        status="pending"
    )
    db.session.add(log_entry)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating initial MessageLog for outgoing text: {str(e)}")

    try:
        logger.info(f"Attempting to send text message to {recipient_phone_number} for client ID {client_profile.user_id}")
        response = whatsapp_service.send_text_message(
            recipient_phone_number=recipient_phone_number,
            message_text=message_text,
            preview_url=preview_url
        )

        if response and "error" not in response and response.get("messages"):
            whatsapp_msg_id = response.get("messages", [{}])[0].get("id")
            log_entry.whatsapp_message_id = whatsapp_msg_id
            log_entry.status = "sent_to_whatsapp"
            db.session.add(log_entry)
            db.session.commit()
            logger.info(f"Text message sent successfully via service. API Response: {response}")
            return jsonify({"message": "Text message sent successfully", "api_response": response, "log_id": log_entry.id}), 200
        else:
            log_entry.status = "failed_to_send"
            log_entry.failure_reason = response.get("error", {}).get("message") if response and response.get("error") else response.get("details", "Unknown error from WhatsApp service")
            db.session.add(log_entry)
            db.session.commit()
            logger.error(f"Failed to send text message via service. Error: {log_entry.failure_reason}")
            return jsonify({
                "message": "Failed to send text message", 
                "error_details": log_entry.failure_reason,
                "status_code_from_meta": response.get("status_code") if response else None
            }), response.get("status_code", 500) if response else 500
            
    except Exception as e:
        log_entry.status = "failed_internal_error"
        log_entry.failure_reason = str(e)
        db.session.add(log_entry)
        db.session.commit()
        logger.error(f"Exception in send_text_message_route: {str(e)}")
        return jsonify({"message": "An internal error occurred while sending the message", "error": str(e)}), 500

@messaging_bp.route("/inbox", methods=["GET"])
@token_required
def get_inbox_messages():
    client_id = request.current_user_id
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    try:
        messages_query = MessageLog.query.filter_by(client_id=client_id, direction="incoming")\
                                         .order_by(desc(MessageLog.created_at))
        
        paginated_messages = messages_query.paginate(page=page, per_page=per_page, error_out=False)
        
        results = []
        for msg in paginated_messages.items:
            results.append({
                "id": msg.id,
                "whatsapp_message_id": msg.whatsapp_message_id,
                "from_phone": msg.sender_phone_number_id, # For incoming, this is the user's number
                "to_phone": msg.recipient_phone_number, # For incoming, this is the app's number
                "content": msg.incoming_message_content,
                "type": msg.message_type,
                "status": msg.status,
                "timestamp": msg.created_at.isoformat(), # WhatsApp timestamp for incoming
            })
        
        return jsonify({
            "messages": results,
            "total_messages": paginated_messages.total,
            "current_page": paginated_messages.page,
            "total_pages": paginated_messages.pages,
            "per_page": paginated_messages.per_page
        }), 200

    except Exception as e:
        logger.error(f"Error fetching inbox messages for client {client_id}: {str(e)}")
        return jsonify({"message": "Failed to retrieve inbox messages", "error": str(e)}), 500

# The main.py file will need to be updated to register this blueprint
# and to initialize the db object properly for models and services.

