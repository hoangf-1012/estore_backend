from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.services.image_service import save_image, delete_image
from app.extensions import db
from app.models import Address, Gender, User, UserRole
from app.utils.security import role_required, active_required

user_bp = Blueprint("user", __name__)

# Cấp quyền Staff cho User (Chỉ cho Admin)
@user_bp.route("/grant-staff/<int:user_id>", methods=["PUT"])
@jwt_required()
@active_required()
@role_required(UserRole.admin)
def grant_staff(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.role == UserRole.staff:
        return jsonify({"message": "User is already a Staff"}), 400

    if user.role == UserRole.admin:
        return jsonify({"message": "Cannot grant Staff role to Admin"}), 400

    user.role = UserRole.staff
    db.session.commit()

    return jsonify({"message": f"User {user.username} has been granted Staff role"}), 200

# Admin cập nhật trạng thái tài khoản user
@user_bp.route("/update-status/<int:user_id>", methods=["PUT"])
@jwt_required()
@active_required()
@role_required(UserRole.admin)
def update_user_status(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    new_status = data.get("is_active")

    if new_status is None:
        return jsonify({"message": "Missing 'is_active' field"}), 400

    user.is_active = new_status
    db.session.commit()

    status_text = "activated" if new_status else "deactivated"
    return jsonify({"message": f"User {user.username} has been {status_text}"}), 200

# Lấy thông tin cá nhân
@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "date_of_birth": user.date_of_birth.strftime("%Y-%m-%d") if user.date_of_birth else None,
        "gender": user.gender.value if user.gender else None,
        "role": user.role.value,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }), 200


# Cập nhật thông tin cá nhân
@user_bp.route("/update-profile", methods=["PUT"])
@jwt_required()
@active_required()
def update_profile():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "phone_number" in data:
        user.phone_number = data["phone_number"]
    if "date_of_birth" in data:
        try:
            user.date_of_birth = datetime.strptime(data["date_of_birth"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
    if "gender" in data:
        if data["gender"] in [gender.value for gender in Gender]:
            user.gender = Gender(data["gender"])
        else:
            return jsonify({"message": "Invalid gender. Choose from 'Male', 'Female', 'Other'"}), 400

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"}), 200

# Cập nhật ảnh đại diện
@user_bp.route("/update-avatar", methods=["PUT"])
@jwt_required()
def update_avatar():
    user_id = get_jwt_identity()["id"]
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    if "avatar" not in request.files:
        return jsonify({"message": "No file uploaded"}), 400

    file = request.files["avatar"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    if user.avatar_url:
        delete_image(user.avatar_url)

    avatar_url, error = save_image(file, folder="uploads/user")
    if error:
        return jsonify({"message": error}), 400

    user.avatar_url = avatar_url
    db.session.commit()

    return jsonify({"message": "Avatar updated successfully", "avatar_url": avatar_url}), 200

# Lấy danh sách địa chỉ
@user_bp.route("/addresses", methods=["GET"])
@jwt_required()
def get_addresses():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

    if not user:
        return jsonify({"message": "User not found"}), 404

    addresses = [
        {
            "id": addr.id,
            "full_name": addr.full_name,
            "phone_number": addr.phone_number,
            "street_address": addr.street_address,
            "district": addr.district,
            "province": addr.province,
            "city": addr.city,
            "state": addr.state,
            "country": addr.country,
            "postal_code": addr.postal_code,
            "is_default": addr.is_default
        }
        for addr in user.addresses
    ]

    return jsonify(addresses), 200

# Thêm địa chỉ mới
@user_bp.route("/add-address", methods=["POST"])
@jwt_required()
@active_required()
def add_address():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    new_address = Address(
        user_id=user.id,
        full_name=data.get("full_name"),
        phone_number=data.get("phone_number"),
        street_address=data.get("street_address"),
        district=data.get("district"),
        province=data.get("province"),
        city=data.get("city"),
        state=data.get("state"),
        country=data.get("country"),
        postal_code=data.get("postal_code"),
        is_default=data.get("is_default", False)
    )

    if new_address.is_default:
        for addr in user.addresses:
            addr.is_default = False

    db.session.add(new_address)
    db.session.commit()

    return jsonify({"message": "Address added successfully"}), 201

# Cập nhật địa chỉ
@user_bp.route("/update-address/<int:address_id>", methods=["PUT"])
@jwt_required()
@active_required()
def update_address(address_id):
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])
    address = Address.query.filter_by(id=address_id, user_id=user.id).first()

    if not address:
        return jsonify({"message": "Address not found"}), 404

    data = request.get_json()
    address.full_name = data.get("full_name", address.full_name)
    address.phone_number = data.get("phone_number", address.phone_number)
    address.street_address = data.get("street_address", address.street_address)
    address.district = data.get("district", address.district)
    address.province = data.get("province", address.province)
    address.city = data.get("city", address.city)
    address.state = data.get("state", address.state)
    address.country = data.get("country", address.country)
    address.postal_code = data.get("postal_code", address.postal_code)
    
    if "is_default" in data:
        if data["is_default"]:
            for addr in user.addresses:
                addr.is_default = False
        address.is_default = data["is_default"]

    db.session.commit()

    return jsonify({"message": "Address updated successfully"}), 200


# Xóa địa chỉ
@user_bp.route("/delete-address/<int:address_id>", methods=["DELETE"])
@jwt_required()
@active_required()
def delete_address(address_id):
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])
    address = Address.query.filter_by(id=address_id, user_id=user.id).first()

    if not address:
        return jsonify({"message": "Address not found"}), 404

    db.session.delete(address)
    db.session.commit()

    return jsonify({"message": "Address deleted successfully"}), 200


# Đặt địa chỉ mặc định
@user_bp.route("/set-default-address/<int:address_id>", methods=["PUT"])
@jwt_required()
@active_required()
def set_default_address(address_id):
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])
    address = Address.query.filter_by(id=address_id, user_id=user.id).first()

    if not address:
        return jsonify({"message": "Address not found"}), 404

    for addr in user.addresses:
        addr.is_default = False

    address.is_default = True
    db.session.commit()

    return jsonify({"message": "Default address set successfully"}), 200

# Lấy danh sách user(Chỉ Admin)
@user_bp.route("/users", methods=["GET"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def get_users():
    role = request.args.get("role", "").strip().lower()
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)

    query = User.query
    if role and role in UserRole.__members__:
        query = query.filter_by(role=UserRole[role])

    users = query.paginate(page=page, per_page=limit, error_out=False)

    result = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active
        }
        for user in users.items
    ]

    return jsonify({
        "total": users.total,
        "page": users.page,
        "per_page": users.per_page,
        "users": result
    }), 200

@user_bp.route('/delete/<int:user_id>', methods=['DELETE'])
@jwt_required()
@active_required()
@role_required(UserRole.admin)
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User does not exist"}), 404
    if user.role == UserRole.admin:
        return jsonify({"message": "Cannot delete admin account"}), 403
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200