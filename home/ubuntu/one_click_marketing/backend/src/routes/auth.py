# backend/src/routes/auth.py

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from ..models.user import User, ClientProfile, db # Assuming db is accessible via ..models.user or a shared app context

# In a typical Flask app, you might use Flask-JWT-Extended for token management
# For simplicity, we'll implement a conceptual token generation/validation here.
# This should be replaced with a robust library in a production system.
import datetime
import jwt # PyJWT library, ensure it's in requirements.txt

# Placeholder for a secret key, this should be configured securely in your app
# For example, app.config["SECRET_KEY"] or os.environ.get("SECRET_KEY")
SECRET_KEY = "your-super-secret-key-please-change-this"

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/v1/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Missing username, email, or password"}), 400

    if User.query.filter_by(username=data["username"]).first() or \
       User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "User already exists"}), 409

    new_user = User(
        username=data["username"],
        email=data["email"],
        role=data.get("role", "client") # Default to client, admin creation might be separate
    )
    new_user.set_password(data["password"])
    
    # Create a client profile by default for new users
    # In a more complex scenario, profile creation might be a separate step or conditional
    new_client_profile = ClientProfile(
        user=new_user, 
        company_name=data.get("company_name", None), # Optional company name
        wallet_balance=0.00 # Initialize wallet balance
    )

    try:
        db.session.add(new_user)
        db.session.add(new_client_profile)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to register user", "error": str(e)}), 500

    return jsonify({"message": "User registered successfully", "user_id": new_user.id}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"message": "Missing username or password"}), 400

    user = User.query.filter_by(username=data["username"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"message": "Invalid username or password"}), 401

    # Generate a token (e.g., JWT)
    token_payload = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24) # Token expires in 24 hours
    }
    try:
        token = jwt.encode(token_payload, SECRET_KEY, algorithm="HS256")
    except Exception as e:
        return jsonify({"message": "Error generating token", "error": str(e)}), 500
    
    return jsonify({
        "message": "Login successful", 
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }), 200

# A protected route example (to be expanded later)
@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Authorization header missing or invalid"}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get("user_id")
        current_user = User.query.get(user_id)
        if not current_user:
            return jsonify({"message": "User not found"}), 404
        
        # Optionally, fetch client profile data if user is a client
        profile_data = None
        if current_user.role == "client" and current_user.client_profile:
            profile_data = {
                "company_name": current_user.client_profile.company_name,
                "wallet_balance": float(current_user.client_profile.wallet_balance) # Ensure float for JSON
            }

        return jsonify({
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "client_profile": profile_data
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"message": "Token processing error", "error": str(e)}), 500

# Logout can be handled client-side by discarding the token.
# If server-side token blacklisting is needed, it would be more complex.
@auth_bp.route("/logout", methods=["POST"])
def logout():
    # For JWT, logout is typically handled by the client deleting the token.
    # If you need server-side blacklisting, you'd implement that here.
    return jsonify({"message": "Logout successful. Please discard your token."}), 200

