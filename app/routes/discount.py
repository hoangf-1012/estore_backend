from datetime import datetime
from app.extensions import db
from flask import jsonify, Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.utils.security import role_required, active_required

from app.models import Discount, UserDiscount, UserRole


discount_bp = Blueprint("discount", __name__)

@discount_bp.route("/list", methods=["GET"])
def get_discounts():
    available_filter = request.args.get("available_filter", "false").lower() == "true"
    if available_filter:
        current_time = datetime.utcnow()
        discounts = Discount.query.filter(Discount.release_date <= current_time, Discount.expiration_date >= current_time).all()
    else:
        discounts = Discount.query.all()

    result = []

    for d in discounts:
        result.append({
            "id": d.id,
            "code": d.code,
            "discount_percent": d.discount_percent,
            "release_date": d.release_date,
            "expiration_date": d.expiration_date,
            "max_users": d.max_users,
            "minimum_order_value": d.minimum_order_value,
            "collected_users": len(d.users_collected),
            "is_valid": d.is_valid()
        })

    return jsonify(result), 200


@discount_bp.route("/collect/<int:discount_id>", methods=["POST"])
@jwt_required()
@active_required()
def collect_discount(discount_id):
    user_id = get_jwt_identity()["id"]
    discount = Discount.query.get(discount_id)

    if not discount:
        return jsonify({"message": "Discount not found"}), 404

    if not discount.is_valid():
        return jsonify({"message": "Discount is no longer available"}), 400

    existing_user_discount = UserDiscount.query.filter_by(user_id=user_id, discount_id=discount_id).first()
    if existing_user_discount:
        return jsonify({"message": "You have already collected this discount"}), 400

    new_user_discount = UserDiscount(user_id=user_id, discount_id=discount_id)
    db.session.add(new_user_discount)
    db.session.commit()

    return jsonify({"message": "Discount collected successfully"}), 201

@discount_bp.route("/my-discounts", methods=["GET"])
@jwt_required()
def get_my_discounts():
    user_id = get_jwt_identity()["id"]
    user_discounts = UserDiscount.query.filter_by(user_id=user_id).all()

    result = []

    for ud in user_discounts:
        if not ud.is_used:
            result.append({
                "discount_id": ud.discount.id,
                "code": ud.discount.code,
                "discount_percent": ud.discount.discount_percent,
                "release_date": ud.discount.release_date,
                "expiration_date": ud.discount.expiration_date,
                "minimum_order_value": ud.discount.minimum_order_value,
                "is_used": False
            })
    return jsonify(result), 200

@discount_bp.route("delete/<int:discount_id>", methods=["DELETE"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def delete_discount(discount_id):
    discount = Discount.query.get(discount_id)

    if not discount:
        return jsonify({"message": "Discount not found"}), 404

    db.session.delete(discount)
    db.session.commit()

    return jsonify({"message": "Discount deleted successfully"}), 200

@discount_bp.route("/create", methods=["POST"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def create_discount():
    data = request.get_json()

    code = data.get("code")
    discount_percent = data.get("discount_percent")
    expiration_date = data.get("expiration_date")
    max_users = data.get("max_users")
    minimum_order_value = data.get("minimum_order_value")

    if not code or not discount_percent or not expiration_date:
        return jsonify({"message": "Missing required fields"}), 400

    if Discount.query.filter_by(code=code).first():
        return jsonify({"message": "Discount code already exists"}), 400

    new_discount = Discount(
        code=code,
        discount_percent=discount_percent,
        release_date=datetime.utcnow(),
        expiration_date=datetime.strptime(expiration_date, "%Y-%m-%d"),
        max_users=max_users,
        minimum_order_value=minimum_order_value
    )

    db.session.add(new_discount)
    db.session.commit()

    return jsonify({"message": "Discount created successfully", "discount_id": new_discount.id}), 201
