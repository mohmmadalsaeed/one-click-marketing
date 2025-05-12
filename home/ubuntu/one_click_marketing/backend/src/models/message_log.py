# backend/src/models/message_log.py

from datetime import datetime
from .user import db # Assuming db is initialized in user.py or a central app file and can be imported

class MessageLog(db.Model):
    __tablename__ = "message_logs"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False) # FK to User table (client user)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=True) # FK to a future Campaigns table
    
    whatsapp_message_id = db.Column(db.String(255), nullable=True, index=True) # Message ID from WhatsApp
    recipient_phone_number = db.Column(db.String(30), nullable=False, index=True)
    sender_phone_number_id = db.Column(db.String(80), nullable=True) # The WhatsApp Business Phone Number ID used to send

    message_type = db.Column(db.String(50), nullable=False) # e.g., "template", "text", "image", "incoming_text"
    direction = db.Column(db.String(10), nullable=False, default="outgoing") # "outgoing" or "incoming"
    
    template_name = db.Column(db.String(255), nullable=True) # If it was a template message
    message_content_rendered = db.Column(db.Text, nullable=True) # For outgoing, the rendered template or text
    incoming_message_content = db.Column(db.Text, nullable=True) # For incoming messages

    status = db.Column(db.String(50), nullable=False, default="pending") 
    # Outgoing statuses: pending, sent, delivered, read, failed, undeliverable
    # Incoming statuses: received, read_by_client (if we implement client read status)
    
    failure_reason = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Numeric(10, 4), nullable=True) # Cost of sending the message

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    sent_at = db.Column(db.DateTime, nullable=True) # Timestamp from WhatsApp when message was sent by them
    delivered_at = db.Column(db.DateTime, nullable=True) # Timestamp from WhatsApp
    read_at = db.Column(db.DateTime, nullable=True) # Timestamp from WhatsApp
    status_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = db.relationship("User", backref=db.backref("message_logs", lazy=True))
    # campaign = db.relationship("Campaign", backref=db.backref("message_logs", lazy=True)) # When Campaign model exists

    def __repr__(self):
        return f"<MessageLog {self.id} to {self.recipient_phone_number} status {self.status}>"

# Note: The Campaign model is referenced but not yet created. 
# It will be created in a later task (Task 008: Create Templates and Messaging System).
# For now, the ForeignKey constraint will be there, but the relationship might not fully resolve until Campaign model is defined.
# Ensure that the db instance is correctly shared across model files, typically by initializing it in your main Flask app file
# and importing it into your model files, or using Flask-Migrate which handles this well.

