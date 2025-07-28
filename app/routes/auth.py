from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt
from app.services.auth_service import generate_verification_code,send_notification, is_verification_code_valid, send_verification_code,is_valid_email
from app.extensions import db, BLACKLIST
from app.models import User, UserRole, Gender
from app.utils.security import active_required
import re

auth_bp = Blueprint("auth", __name__)

# Đăng ký tài khoản (Chỉ cho phép `Customer`)
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")
    phone_number = data.get("phone_number")



    if not is_valid_email(email):
        return jsonify({"message": "Invalid email"}), 400

    if not email or not password:
        return jsonify({"message": "Missing required fields"}), 400
    
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400

    if User.query.filter((User.email == email) | (User.username == username)).first():
        return jsonify({"message": "Email or Username already exists"}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(
        full_name=full_name,
        username=username,
        email=email,
        password_hash=hashed_password,
        phone_number=phone_number,
        role=UserRole.customer 
    )
    
    if "gender" in data:
        if data["gender"] in [gender.value for gender in Gender]:
            new_user.gender = Gender(data.get("gender"))
        else:
            return jsonify({"message": "Invalid gender. Choose from 'Male', 'Female', 'Other'"}), 400
    print(new_user.gender)
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

# Đăng nhập
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    identity = data.get("identity")
    password = data.get("password")

    user = User.query.filter((User.email == identity) | (User.username == identity)).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"message": "Account is inactive"}), 403

    access_token = create_access_token(identity={"id": user.id, "role": user.role.value},expires_delta=timedelta(days=7))
    return jsonify({"access_token": access_token}), 200

# Đăng xuất
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    BLACKLIST.add(jti)
    return jsonify({"message": "Successfully logged out"}), 200


# API Quên mật khẩu - Gửi mã reset qua email
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Email not found"}), 404

    reset_code = generate_verification_code()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    user.verification_code = reset_code
    user.verification_code_expires_at = expires_at
    db.session.commit()

    send_verification_code(email, reset_code, purpose="password_reset")

    return jsonify({"message": "Reset code sent to email"}), 200

# API Đặt lại mật khẩu
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email")
    reset_code = data.get("reset_code")
    new_password = data.get("new_password")


    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active or not user.verification_code or not user.verification_code_expires_at or not is_verification_code_valid(user, reset_code):
        return jsonify({"message": "Invalid or expired reset code"}), 403

    if len(new_password) < 6:
        return jsonify({"message": "New password must be at least 6 characters long"}), 422

    user.password_hash = generate_password_hash(new_password)
    user.verification_code = None
    user.verification_code_expires_at = None
    db.session.commit()

    send_notification(email, "Password Reset Successful", "Your password has been reset successfully. If you did not request this, please contact support.")

    return jsonify({"message": "Password reset successfully"}), 200

# API Thay đổi mật khẩu
@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
@active_required()
def change_password():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not check_password_hash(user.password_hash, old_password):
        return jsonify({"message": "Incorrect old password"}), 400

    if len(new_password) < 6:
        return jsonify({"message": "New password must be at least 6 characters long"}), 400
    if old_password == new_password:
        return jsonify({"message": "New password cannot be the same as the old password"}), 400

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200

# API Yêu cầu thay đổi email
@auth_bp.route("/request-email-change", methods=["POST"])
@jwt_required()
@active_required()
def request_email_change():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

    if not user:
        return jsonify({"message": "User not found"}), 404

        
    if user.id != identity["id"]:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    new_email = data.get("new_email")

    if User.query.filter_by(email=new_email).first():
        return jsonify({"message": "Email already exists"}), 400

    confirmation_code = generate_verification_code()
    user.verification_code = confirmation_code
    user.verification_code_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()

    send_verification_code(new_email, confirmation_code, purpose="email_change")

    return jsonify({"message": "Confirmation code sent to your new email"}), 200


# API Xác nhận thay đổi email
@auth_bp.route("/change-email", methods=["PUT"])
@jwt_required()
@active_required()
def change_email():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.id != identity["id"]:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    new_email = data.get("new_email")
    confirmation_code = data.get("confirmation_code")
    
    
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, new_email):
        return jsonify({"message": "Invalid email format"}), 422 

    if new_email == user.email:
        return jsonify({"message": "New email cannot be the same as current email"}), 409

    if not is_verification_code_valid(user, confirmation_code):
        return jsonify({"message": "Invalid or expired confirmation code"}), 400

    if User.query.filter_by(email=new_email).first():
        return jsonify({"message": "Email already exists"}), 400

    old_email = user.email 

    user.email = new_email
    user.verification_code = None 
    user.verification_code_expires_at = None
    db.session.commit()

    send_notification(old_email, "Email Changed Successfully", "Your email has been changed successfully. If you did not request this, please contact support.")

    return jsonify({"message": "Email updated successfully"}), 200

# Thay đổi Username
@auth_bp.route("/change-username", methods=["PUT"])
@jwt_required()
@active_required()
def change_username():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

    if not user:
        return jsonify({"message": "User not found"}), 404
    
    if user.id != identity["id"]:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    new_username = data.get("new_username")

    if User.query.filter_by(username=new_username).first():
        return jsonify({"message": "Username already exists"}), 400

    user.username = new_username
    db.session.commit()

    return jsonify({"message": "Username updated successfully"}), 200