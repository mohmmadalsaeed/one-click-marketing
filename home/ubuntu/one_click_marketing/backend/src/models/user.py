# backend/src/models/user.py

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import decimal # For precise decimal arithmetic for currency

# It's a common practice to initialize db in a separate file or in the main app, 
# but for simplicity in this step, we'll assume db is initialized and passed or imported.
# In a real Flask app, you'd typically have a db object from your main app instance.
# For now, let's define a placeholder db. This will be refined when integrating with main.py

db = SQLAlchemy() # This will be replaced by the actual db instance from main.py

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Increased length for stronger hashes
    role = db.Column(db.String(20), nullable=False, default="client") # Roles: 'client', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to ClientProfile (one-to-one)
    client_profile = db.relationship("ClientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

class ClientProfile(db.Model):
    __tablename__ = "client_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    company_name = db.Column(db.String(120), nullable=True)
    
    # Meta/WhatsApp Credentials
    meta_access_token_encrypted = db.Column(db.String(1024), nullable=True) 
    meta_phone_number_id = db.Column(db.String(80), nullable=True)
    meta_waba_id = db.Column(db.String(80), nullable=True) # WhatsApp Business Account ID

    # Wallet Balance - Using Numeric for precision with currency
    wallet_balance = db.Column(db.Numeric(10, 2), nullable=False, default=decimal.Decimal("0.00"))
    currency = db.Column(db.String(10), nullable=False, default="USD") # Default currency for the wallet

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to User
    user = db.relationship("User", back_populates="client_profile")

    def __repr__(self):
        return f"<ClientProfile for User ID {self.user_id}, Balance: {self.wallet_balance} {self.currency}>"

