# backend/src/services/whatsapp_service.py

import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The Meta Graph API endpoint for sending messages
WHATSAPP_API_VERSION = "v19.0" # It's good practice to use a specific version

class WhatsAppService:
    def __init__(self, access_token, phone_number_id):
        """
        Initializes the WhatsAppService with the client's access token and phone number ID.
        Args:
            access_token (str): The client's Meta Graph API access token.
            phone_number_id (str): The client's WhatsApp Business Phone Number ID.
        """
        # TODO: Implement proper decryption for access_token if it's stored encrypted
        self.access_token = access_token 
        self.phone_number_id = phone_number_id
        self.base_url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{self.phone_number_id}/messages"

    def send_template_message(self, recipient_phone_number, template_name, language_code="en_US", components=None):
        """
        Sends a template message to a recipient.
        Args:
            recipient_phone_number (str): The recipient's phone number with country code (e.g., "15550001234").
            template_name (str): The name of the pre-approved message template.
            language_code (str): The language code for the template (e.g., "en_US", "ar").
            components (list, optional): A list of components for template variables (header, body, buttons).
                                         Example: [{
                                             "type": "body",
                                             "parameters": [
                                                 {"type": "text", "text": "Value1"},
                                                 {"type": "text", "text": "Value2"}
                                             ]
                                         }]
        Returns:
            dict: The JSON response from the Meta API or an error dictionary.
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_phone_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        if components:
            payload["template"]["components"] = components

        logger.info(f"Sending template message '{template_name}' to {recipient_phone_number}")
        try:
            response = requests.post(self.base_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
            logger.info(f"Message sent successfully. Response: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            if e.response is not None:
                logger.error(f"Error response content: {e.response.text}")
                return {"error": str(e), "status_code": e.response.status_code, "details": e.response.text}
            return {"error": str(e), "status_code": None, "details": "Network error or no response"}

    def send_text_message(self, recipient_phone_number, message_text, preview_url=False):
        """
        Sends a free-form text message to a recipient (only within 24-hour customer care window).
        Args:
            recipient_phone_number (str): The recipient's phone number.
            message_text (str): The text message content.
            preview_url (bool): Whether to show a URL preview if the message contains a URL.
        Returns:
            dict: The JSON response from the Meta API or an error dictionary.
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_phone_number,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": message_text
            }
        }
        logger.info(f"Sending text message to {recipient_phone_number}")
        try:
            response = requests.post(self.base_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            logger.info(f"Text message sent successfully. Response: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending WhatsApp text message: {e}")
            if e.response is not None:
                logger.error(f"Error response content: {e.response.text}")
                return {"error": str(e), "status_code": e.response.status_code, "details": e.response.text}
            return {"error": str(e), "status_code": None, "details": "Network error or no response"}

# Example Usage (for testing, not to be run directly here usually):
# if __name__ == "__main__":
#     # Replace with actual test credentials and recipient
#     test_access_token = "YOUR_TEST_ACCESS_TOKEN"
#     test_phone_number_id = "YOUR_TEST_PHONE_NUMBER_ID"
#     test_recipient_phone = "RECIPIENT_PHONE_NUMBER_WITH_COUNTRY_CODE"

#     service = WhatsAppService(access_token=test_access_token, phone_number_id=test_phone_number_id)
    
#     # Test sending a template message (assuming 'hello_world' template exists)
#     template_response = service.send_template_message(test_recipient_phone, "hello_world")
#     print("Template Message Response:", template_response)

#     # Test sending a text message (only works if a 24-hour window is open with the recipient)
#     # text_response = service.send_text_message(test_recipient_phone, "This is a test text message from the service.")
#     # print("Text Message Response:", text_response)

