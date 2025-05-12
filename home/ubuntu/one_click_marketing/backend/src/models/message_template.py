# backend/src/models/message_template.py

from datetime import datetime
from .user import db  # Assuming db is initialized in user.py or a central app file

class MessageTemplate(db.Model):
    __tablename__ = "message_templates"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False) # FK to User table (client user)
    
    template_name = db.Column(db.String(255), nullable=False) # Name as recognized by Meta, must be unique per client WABA
    # It is Meta that approves and manages the actual template structure (category, body, header, footer, buttons).
    # This model stores a reference to the Meta-approved template and its local configuration.
    
    meta_template_id = db.Column(db.String(255), nullable=True) # Optional: If Meta provides an ID for the template itself
    category = db.Column(db.String(50), nullable=True) # E.g., MARKETING, UTILITY, AUTHENTICATION (as per Meta categories)
    language_code = db.Column(db.String(10), nullable=False, default="en_US") # Default language for this template entry
    
    # Store the structure of the template as defined in Meta, perhaps as JSON
    # This helps in rendering the template with variables on the frontend for preview/management
    # and for constructing the API call.
    # Example: {"header": {"type": "TEXT", "text": "Hello {{1}}"}, "body": {"text": "Your code is {{2}}."}, "buttons": [{"type": "QUICK_REPLY", "text": "Reply Now"}]}
    template_structure_json = db.Column(db.Text, nullable=True) 
    
    # Variables expected by the template, could be derived from template_structure_json or stored separately for validation
    # Example: ["customer_name", "order_id", "tracking_link"]
    variables_expected_json = db.Column(db.Text, nullable=True) # JSON array of variable names or placeholders like {{1}}, {{2}}

    status = db.Column(db.String(50), nullable=False, default="PENDING_META_APPROVAL") 
    # Local status: DRAFT, PENDING_META_APPROVAL, APPROVED_BY_META, REJECTED_BY_META, PAUSED, DISABLED
    meta_rejection_reason = db.Column(db.Text, nullable=True) # If rejected by Meta

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    client = db.relationship("User", backref=db.backref("message_templates", lazy=True))

    def __repr__(self):
        return f"<MessageTemplate {self.id} 	{self.template_name}	 for Client {self.client_id}>"

# Note: Clients will typically create templates via the Meta Business Manager or through an API if available.
# This system will primarily allow clients to *register* their Meta-approved templates for use in campaigns,
# or potentially guide them through a creation process that mirrors Meta requirements.
# The `status` field here reflects both local management and Meta's approval status.

