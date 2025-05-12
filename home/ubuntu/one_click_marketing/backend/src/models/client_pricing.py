# backend/src/models/client_pricing.py

from datetime import datetime
from .user import db # Assuming db is initialized
import decimal

class ClientPricing(db.Model):
    __tablename__ = "client_pricing"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True) # One-to-one or one-to-many if multiple pricing tiers per client
    
    # Example: Store a default price per message for this client.
    # This can be expanded to support pricing based on message type, destination, volume, etc.
    # For simplicity, starting with a single rate per message.
    price_per_message = db.Column(db.Numeric(10, 4), nullable=False, default=decimal.Decimal("0.0100")) # e.g., $0.0100 per message
    currency = db.Column(db.String(10), nullable=False, default="USD") # Currency for this pricing

    # Potentially add fields for different message types or destinations if needed
    # price_per_text_message = db.Column(db.Numeric(10, 4), nullable=True)
    # price_per_media_message = db.Column(db.Numeric(10, 4), nullable=True)
    # price_per_template_message_utility = db.Column(db.Numeric(10, 4), nullable=True)
    # price_per_template_message_marketing = db.Column(db.Numeric(10, 4), nullable=True)

    # Fields for volume-based discounts could also be added here or in a related table.

    notes = db.Column(db.Text, nullable=True) # Admin notes about this client's pricing

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    # Assuming one-to-one with User (Client) for now for a single pricing setting per client.
    # If a client can have multiple pricing schemes, this would be a ForeignKey to ClientProfile and User would have a list of ClientPricing.
    client = db.relationship("User", backref=db.backref("pricing_settings", uselist=False, lazy="joined"))

    def __repr__(self):
        return f"<ClientPricing for Client ID {self.client_id}, Price: {self.price_per_message} {self.currency}>"

# This model will be used by an admin interface to set prices.
# The WalletTransaction creation logic (e.g., in ReportingService or when sending messages)
# will need to fetch this price to calculate the cost for the client.

