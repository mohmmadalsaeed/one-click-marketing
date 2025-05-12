# backend/src/routes/admin.py

from flask import Blueprint, request, jsonify
from ..models.user import User, ClientProfile, db
from ..routes.auth import SECRET_KEY # Import SECRET_KEY for token decoding
import jwt # PyJWT library

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/api/v1/admin")

# Decorator to protect admin routes
def admin_required(fn):
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Authorization header missing or invalid"}), 401

        token = auth_header.split(" ")[1]
        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token.get("user_id")
            role = decoded_token.get("role")
            
            if role != "admin":
                return jsonify({"message": "Admin access required"}), 403
            
            current_user = User.query.get(user_id)
            if not current_user or current_user.role != "admin":
                return jsonify({"message": "Admin user not found or invalid role"}), 403
            
            # Pass the current admin user to the route if needed, though not used in these examples
            # request.current_admin_user = current_user 
            
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"message": "Token processing error", "error": str(e)}), 500
        
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__ # Preserve original function name for Flask
    return wrapper

@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    try:
        users = User.query.all()
        user_list = []
        for user in users:
            client_data = None
            if user.client_profile:
                client_data = {
                    "company_name": user.client_profile.company_name,
                    "wallet_balance": float(user.client_profile.wallet_balance),
                    "meta_phone_number_id": user.client_profile.meta_phone_number_id
                }
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "client_profile": client_data
            })
        return jsonify(user_list), 200
    except Exception as e:
        return jsonify({"message": "Failed to retrieve users", "error": str(e)}), 500

@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        client_data = None
        if user.client_profile:
            client_data = {
                "company_name": user.client_profile.company_name,
                "wallet_balance": float(user.client_profile.wallet_balance),
                "meta_phone_number_id": user.client_profile.meta_phone_number_id,
                "meta_api_key_present": bool(user.client_profile.meta_api_key_encrypted) # Indicate if key is set
            }

        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "client_profile": client_data
        }), 200
    except Exception as e:
        return jsonify({"message": "Failed to retrieve user details", "error": str(e)}), 500

@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        if "email" in data:
            existing_email_user = User.query.filter(User.email == data["email"], User.id != user_id).first()
            if existing_email_user:
                return jsonify({"message": "Email already in use by another account"}), 409
            user.email = data["email"]
        
        if "role" in data and data["role"] in ["client", "admin"]:
            user.role = data["role"]
        
        # Update client profile if it exists and data is provided
        if user.client_profile and "client_profile" in data:
            profile_data = data["client_profile"]
            if "company_name" in profile_data:
                user.client_profile.company_name = profile_data["company_name"]
            if "wallet_balance" in profile_data:
                try:
                    user.client_profile.wallet_balance = float(profile_data["wallet_balance"])
                except ValueError:
                    return jsonify({"message": "Invalid wallet balance format"}), 400
        
        user.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update user", "error": str(e)}), 500

@admin_bp.route("/users/<int:user_id>/wallet", methods=["POST"])
@admin_required
def adjust_wallet(user_id):
    data = request.get_json()
    if not data or "amount" not in data or "type" not in data:
        return jsonify({"message": "Missing amount or transaction type (e.g., top_up, deduction)"}), 400

    try:
        amount = float(data["amount"])
        transaction_type = data["type"]
    except ValueError:
        return jsonify({"message": "Invalid amount format"}), 400

    user = User.query.get(user_id)
    if not user or not user.client_profile:
        return jsonify({"message": "Client profile not found for this user"}), 404

    try:
        if transaction_type == "top_up":
            user.client_profile.wallet_balance += amount
        elif transaction_type == "deduction":
            if user.client_profile.wallet_balance < amount:
                return jsonify({"message": "Insufficient wallet balance for deduction"}), 400
            user.client_profile.wallet_balance -= amount
        else:
            return jsonify({"message": "Invalid transaction type. Use 'top_up' or 'deduction'."}), 400
        
        # Here you would also create a FinancialTransaction record
        # For now, just updating the balance
        db.session.commit()
        return jsonify({
            "message": f"Wallet balance updated successfully. New balance: {user.client_profile.wallet_balance:.2f}"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to adjust wallet balance", "error": str(e)}), 500

# Note: Deleting users can have cascading effects and should be handled carefully (e.g., soft delete)
# This is a hard delete for demonstration.
@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        # If user has a client profile, it will be cascade deleted due to model definition
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete user", "error": str(e)}), 500

# Placeholder for creating an admin user. In a real app, this might be a CLI command or a secure initial setup.
@admin_bp.route("/create-admin", methods=["POST"])
# This route should be heavily protected or used only for initial setup.
# For now, let's assume it's an internal/setup route not requiring JWT admin auth for creation itself.
def create_admin_user():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Missing username, email, or password for admin creation"}), 400

    if User.query.filter_by(username=data["username"]).first() or \
       User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Admin user with this username/email already exists"}), 409

    admin_user = User(
        username=data["username"],
        email=data["email"],
        role="admin"
    )
    admin_user.set_password(data["password"])
    
    # Admins typically don't have a client profile in this structure
    try:
        db.session.add(admin_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create admin user", "error": str(e)}), 500

    return jsonify({"message": "Admin user created successfully", "user_id": admin_user.id}), 201

