# backend/src/routes/meta_integration.py

from flask import Blueprint, request, jsonify
from ..models.user import User, ClientProfile, db
from ..models.message_log import MessageLog # Import MessageLog model
from ..routes.auth import SECRET_KEY # For token decoding to identify the user
import jwt # PyJWT library
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# In a real application, use a proper encryption library like Fernet from cryptography
# For now, this is a placeholder for where encryption/decryption would occur.
# Storing sensitive tokens requires robust encryption at rest.

meta_bp = Blueprint("meta_bp", __name__, url_prefix="/api/v1/meta")

# Decorator to protect routes, ensuring user is authenticated
def token_required(fn):
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Authorization header missing or invalid"}), 401

        token = auth_header.split(" ")[1]
        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.current_user_id = decoded_token.get("user_id")
            current_user = User.query.get(request.current_user_id)
            if not current_user:
                return jsonify({"message": "User not found"}), 401
            if not current_user.client_profile:
                 return jsonify({"message": "Client profile not found for this user"}), 404
            request.current_client_profile = current_user.client_profile

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        except Exception as e:
            logger.error(f"Token processing error: {str(e)}")
            return jsonify({"message": "Token processing error", "error": str(e)}), 500
        
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@meta_bp.route("/credentials", methods=["POST", "PUT"])
@token_required
def manage_meta_credentials():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    access_token = data.get("access_token")
    phone_number_id = data.get("phone_number_id")
    waba_id = data.get("waba_id")

    if not access_token or not phone_number_id or not waba_id:
        return jsonify({"message": "Missing one or more required credentials: access_token, phone_number_id, waba_id"}), 400

    client_profile = request.current_client_profile

    try:
        client_profile.meta_access_token_encrypted = access_token 
        client_profile.meta_phone_number_id = phone_number_id
        client_profile.meta_waba_id = waba_id
        
        db.session.commit()
        return jsonify({"message": "Meta API credentials updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update Meta API credentials: {str(e)}")
        return jsonify({"message": "Failed to update Meta API credentials", "error": str(e)}), 500

@meta_bp.route("/credentials", methods=["GET"])
@token_required
def get_meta_credentials_status():
    client_profile = request.current_client_profile
    
    credentials_set = bool(client_profile.meta_access_token_encrypted and 
                           client_profile.meta_phone_number_id and 
                           client_profile.meta_waba_id)
    
    return jsonify({
        "credentials_set": credentials_set,
        "phone_number_id": client_profile.meta_phone_number_id if credentials_set else None,
        "waba_id": client_profile.meta_waba_id if credentials_set else None
    }), 200

@meta_bp.route("/webhook", methods=["GET", "POST"])
def whatsapp_webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        expected_verify_token = "ONE_CLICK_MARKETING_VERIFY_TOKEN" # Make this configurable via env var
        
        if verify_token == expected_verify_token and challenge:
            logger.info("Webhook verified successfully.")
            return challenge, 200
        else:
            logger.warning(f"Webhook verification failed. Received token: {verify_token}")
            return jsonify({"message": "Invalid verification token or challenge missing"}), 403

    elif request.method == "POST":
        data = request.get_json()
        logger.info(f"Received WhatsApp Webhook: {json.dumps(data, indent=2)}")

        try:
            if data.get("object") == "whatsapp_business_account":
                for entry in data.get("entry", []):
                    for change in entry.get("changes", []):
                        value = change.get("value", {})
                        metadata = value.get("metadata", {})
                        
                        # Determine client_id based on WABA ID or phone_number_id
                        # This part needs careful implementation to map webhook to your internal client_id
                        # Assuming metadata.phone_number_id is the recipient of the webhook (i.e., your app's WABA phone number)
                        client_waba_id = entry.get("id") # This is the WABA ID
                        client_profile = ClientProfile.query.filter_by(meta_waba_id=client_waba_id).first()
                        if not client_profile:
                            logger.warning(f"No client profile found for WABA ID: {client_waba_id}. Skipping webhook processing.")
                            continue
                        
                        client_id = client_profile.user_id
                        sender_phone_number_id_from_meta = metadata.get("phone_number_id") # This is the app's sending number ID

                        # Handle message status updates
                        if value.get("statuses"):
                            for status_update in value.get("statuses", []):
                                whatsapp_msg_id = status_update.get("id")
                                status = status_update.get("status")
                                timestamp = datetime.fromtimestamp(int(status_update.get("timestamp")))
                                
                                msg_log = MessageLog.query.filter_by(whatsapp_message_id=whatsapp_msg_id, client_id=client_id).first()
                                if msg_log:
                                    msg_log.status = status
                                    msg_log.status_updated_at = datetime.utcnow()
                                    if status == "sent":
                                        msg_log.sent_at = timestamp
                                    elif status == "delivered":
                                        msg_log.delivered_at = timestamp
                                    elif status == "read":
                                        msg_log.read_at = timestamp
                                    elif status == "failed":
                                        msg_log.failure_reason = status_update.get("errors", [{}])[0].get("title", "Unknown error")
                                    db.session.add(msg_log)
                                else:
                                    logger.warning(f"MessageLog not found for status update. WhatsApp ID: {whatsapp_msg_id}, Client ID: {client_id}")
                        
                        # Handle incoming messages
                        if value.get("messages"):
                            for message_data in value.get("messages", []):
                                incoming_msg_id = message_data.get("id")
                                from_phone = message_data.get("from")
                                timestamp = datetime.fromtimestamp(int(message_data.get("timestamp")))
                                msg_type = message_data.get("type")
                                content = None

                                if msg_type == "text":
                                    content = message_data.get("text", {}).get("body")
                                elif msg_type == "image":
                                    content = f"Image received (ID: {message_data.get('image',{}).get('id')})" # Store ID or caption
                                # Add more types as needed (audio, video, document, location, contacts, interactive)
                                else:
                                    content = f"Unsupported message type: {msg_type}"

                                if content:
                                    new_log = MessageLog(
                                        client_id=client_id,
                                        whatsapp_message_id=incoming_msg_id,
                                        recipient_phone_number=sender_phone_number_id_from_meta, # The app's number received the message
                                        sender_phone_number_id=from_phone, # The user who sent the message
                                        message_type=f"incoming_{msg_type}",
                                        direction="incoming",
                                        incoming_message_content=content,
                                        status="received", # Or map to a specific incoming status
                                        created_at=timestamp, # Use WhatsApp timestamp for creation
                                        status_updated_at=datetime.utcnow()
                                    )
                                    db.session.add(new_log)
                                    logger.info(f"Logged incoming message from {from_phone} for client ID {client_id}")
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing WhatsApp webhook: {str(e)}", exc_info=True)
            # Still return 200 to Meta, as they will retry if they don't get it.
            # Log the error for debugging.
        
        return jsonify({"status": "success"}), 200

    return jsonify({"message": "Method not allowed"}), 405

