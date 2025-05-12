# backend/src/models/wallet_transaction.py

from datetime import datetime
from .user import db # Assuming db is initialized
from enum import Enum as PyEnum

class TransactionType(PyEnum):
    TOP_UP = "TOP_UP" # Client adds funds to their wallet
    MESSAGE_COST = "MESSAGE_COST" # Cost deducted for sending a message
    CAMPAIGN_COST = "CAMPAIGN_COST" # Bulk cost for a campaign (could be sum of message costs)
    REFUND = "REFUND" # Refund to client wallet
    SERVICE_FEE = "SERVICE_FEE" # Any service fee charged
    OTHER = "OTHER" # Other types of transactions

class WalletTransaction(db.Model):
    __tablename__ = "wallet_transactions"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=True) # Optional, if related to a campaign
    message_log_id = db.Column(db.Integer, db.ForeignKey("message_log.id"), nullable=True) # Optional, if related to a specific message
    
    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)
    amount = db.Column(db.Float, nullable=False) # Positive for credits (top-up), negative for debits (costs)
    currency = db.Column(db.String(10), nullable=False, default="USD") # Assuming a default currency
    
    description = db.Column(db.Text, nullable=True) # E.g., "Top-up via Stripe", "Cost for campaign X", "Message to +12345"
    reference_id = db.Column(db.String(255), nullable=True) # E.g., Stripe transaction ID, internal reference
    
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    client = db.relationship("User", backref=db.backref("wallet_transactions", lazy="dynamic"))
    campaign = db.relationship("Campaign", backref=db.backref("wallet_transactions", lazy="dynamic"))
    message_log = db.relationship("MessageLog", backref=db.backref("wallet_transactions", lazy="dynamic"))

    def __repr__(self):
        return f"<WalletTransaction {self.id} 	{self.transaction_type.value}	 Amount: {self.amount} {self.currency} for Client {self.client_id}>"

# We also need to add a wallet balance to the ClientProfile model.
# This will be updated by these transactions.
# Let's assume ClientProfile in user.py will be updated to include:
# current_wallet_balance = db.Column(db.Float, nullable=False, default=0.0)

