# backend/src/models/campaign.py

from datetime import datetime
from .user import db  # Assuming db is initialized
from .message_template import MessageTemplate # For linking to a template

class Campaign(db.Model):
    __tablename__ = "campaigns"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey("message_templates.id"), nullable=False)
    
    campaign_name = db.Column(db.String(255), nullable=False)
    
    # Audience can be complex. For now, let's assume a simple list of phone numbers or a segment ID.
    # A more robust solution might involve a separate Audience model or integration with a CRM.
    # For simplicity, storing as JSON text for now, e.g., ["+15551234567", "+15557654321"]
    # Or it could be a reference to a contact list/group model if we build that.
    audience_json = db.Column(db.Text, nullable=True) # JSON array of phone numbers or contact group IDs
    
    # Personalization data: A JSON object where keys are recipient phone numbers (or other identifiers)
    # and values are objects પાણીng variable values for that recipient.
    # E.g., {"+15551234567": {"name": "John", "date": "2023-10-26"}, ...}
    # This might become very large. For large campaigns, consider alternative storage or processing.
    personalization_data_json = db.Column(db.Text, nullable=True) 

    scheduled_at = db.Column(db.DateTime, nullable=True) # If null, send immediately (or requires manual trigger)
    # Actual send time might differ slightly due to processing delays.
    actual_sent_at = db.Column(db.DateTime, nullable=True) # When the campaign processing actually started
    
    status = db.Column(db.String(50), nullable=False, default="DRAFT") 
    # DRAFT, SCHEDULED, SENDING, COMPLETED, PAUSED, FAILED, CANCELLED
    
    # Statistics (can be aggregated from MessageLog or stored here for quick access)
    total_recipients = db.Column(db.Integer, default=0)
    messages_sent_count = db.Column(db.Integer, default=0)
    messages_delivered_count = db.Column(db.Integer, default=0)
    messages_read_count = db.Column(db.Integer, default=0)
    messages_failed_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = db.relationship("User", backref=db.backref("campaigns", lazy=True))
    template = db.relationship("MessageTemplate", backref=db.backref("campaigns", lazy=True))

    # Message logs for this campaign can be queried via MessageLog.campaign_id

    def __repr__(self):
        return f"<Campaign {self.id} 	{self.campaign_name}	 for Client {self.client_id}>"

# Need to update MessageLog model to include nullable campaign_id if not already done.
# The `message_log.py` already has `campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=True)`
# so that part is covered.

