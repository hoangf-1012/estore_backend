from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import CartItem, Product
from app.services.product_service import get_product_with_details
from app.extensions import db
from app.utils.security import active_required

cart_bp = Blueprint("cart", __name__)

@cart_bp.route("/get", methods=["GET"])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()["id"]
    if not user_id:
        return jsonify({"error": "invalid user"}), 403

    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    result = [
        {
            "id": item.id,
            "product": get_product_with_details(item.product_id),
            "quantity": item.quantity
        }
        for item in cart_items
    ]
    return jsonify(result), 200

@cart_bp.route("/add", methods=["POST"])
@jwt_required()
@active_required()
def add_to_cart():
    data = request.get_json()
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    user_id = get_jwt_identity()["id"]

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    product = Product.query.get(product_id)
    if not product or product.stock < quantity:
        return jsonify({"error": "Product not available or insufficient stock"}), 400

    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item and cart_item.user_id != user_id:
        return jsonify({"message": "Forbidden: invalid user"}), 403

    if cart_item:
        if product.stock < cart_item.quantity + quantity:
            return jsonify({"error": "Not enough stock available"}), 400
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)

    db.session.commit()
    return jsonify({"message": "Product added to cart"}), 201


@cart_bp.route("/update/<int:cart_item_id>", methods=["PUT"])
@jwt_required()
@active_required()
def update_cart(cart_item_id):
    data = request.get_json()
    quantity = data.get("quantity")

    if quantity is None or not isinstance(quantity, int) or quantity < 1:
        return jsonify({"error": "Invalid quantity"}), 400

    cart_item = CartItem.query.get(cart_item_id)
    if not cart_item:
        return jsonify({"error": "Cart item not found"}), 404

    identity = get_jwt_identity()
    if cart_item.user_id != identity["id"]:
        return jsonify({"message": "Forbidden: invalid user"}), 403

    product = Product.query.get(cart_item.product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    if quantity > product.stock:
        return jsonify({"error": "Insufficient stock"}), 400

    cart_item.quantity = quantity
    db.session.commit()
    return jsonify({"message": "Cart updated successfully"}), 200


@cart_bp.route("/delete/<int:cart_item_id>", methods=["DELETE"])
@jwt_required()
@active_required()
def remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get(cart_item_id)

    if not cart_item:
        return jsonify({"error": "Cart item not found"}), 404

    identity = get_jwt_identity()
    if cart_item.user_id != identity["id"]:
        return jsonify({"message": "Forbidden: invalid user"}), 403


    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({"message": "Product removed from cart"}), 200

@cart_bp.route("/list", methods=["GET"])
@jwt_required()
@active_required()
def get_cart_items():
    cart_items = CartItem.query.all()
    result = []
    for item in cart_items:
        result.append({
            "cart_item_id": item.id,
            "user_id": item.user_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
        })

    return jsonify({"cart_items": result}), 200
