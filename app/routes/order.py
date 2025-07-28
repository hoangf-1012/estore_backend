from app.extensions import db
from flask import jsonify, Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import CartItem, Order, OrderItem, OrderStatus, User, UserDiscount, UserRole, Product
from app.utils.security import role_required, active_required

order_bp = Blueprint("order", __name__)

from app.services.order_service import  calculate_order_items_total, get_order_item_image

@order_bp.route("/create", methods=["POST"])
@jwt_required()
@active_required()
def create_order():
    user_id = get_jwt_identity()["id"]
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    order_items_data = data.get("order_items", [])

    if not order_items_data:
        return jsonify({"message": "No order items provided"}), 400

    order_items, total_price, error = calculate_order_items_total(order_items_data, user_id)
    if error:
        return jsonify({"message": error}), 400

    new_order = Order(user_id=user_id, total_price=total_price, status=OrderStatus.pending)
    db.session.add(new_order)
    db.session.commit()

    for item in order_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            price=item["price"],
            discount_id=item["discount_id"]
        )
        db.session.add(order_item)
    db.session.commit()

    for item in order_items:
        product = Product.query.get(item["product_id"])
        if product:
            product.stock -= item["quantity"]
            db.session.commit()

    for item in order_items:
        cart_item = CartItem.query.filter_by(user_id=user_id, product_id=item["product_id"]).first()
        db.session.delete(cart_item)
    db.session.commit()

    return jsonify({
        "message": "Order created successfully",
        "order_id": new_order.id,
        "total_price": total_price
    }), 201


@order_bp.route("/cancel/<int:order_id>", methods=["PUT"])
@jwt_required()
@active_required()
def cancel_order(order_id):
    user_id = get_jwt_identity()["id"]
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return jsonify({"message": "Order not found"}), 404

    if order.status != OrderStatus.pending:
        return jsonify({"message": "Order cannot be canceled"}), 400

    order.status = OrderStatus.canceled
    db.session.commit()

    return jsonify({"message": "Order canceled successfully"}), 200


@order_bp.route("/update-status/<int:order_id>", methods=["PUT"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get("status")

    if new_status not in [status.value for status in OrderStatus]:
        return jsonify({"message": "Invalid order status"}), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"message": "Order not found"}), 404

    order.status = OrderStatus[new_status.lower()]
    db.session.commit()

    if new_status == OrderStatus.canceled:
        user_discount = UserDiscount.query.filter_by(user_id=order.user_id, discount_id=order.discount_id, is_used=True).first()
        if user_discount:
            user_discount.is_used = False
            db.session.commit()
    return jsonify({"message": "Order status updated successfully"}), 200

@order_bp.route("/list", methods=["GET"])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()["id"]
    orders = Order.query.filter_by(user_id=user_id).all()

    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "total_price": order.total_price,
            "status": order.status.value,
            "created_at": order.created_at,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "discount_id": item.discount_id,
                    "product_image": get_order_item_image(item.product_id),
                    "product_name": Product.query.get(item.product_id).name,
                    "price": item.price
                } for item in order.order_items
            ]
        })
    return jsonify(result), 200

@order_bp.route("/admin/list", methods=["GET"])
@jwt_required()
@active_required()
@role_required(UserRole.admin,UserRole.staff)
def admin_get_orders():
    orders = Order.query.all()

    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "total_price": order.total_price,
            "status": order.status.value,
            "created_at": order.created_at,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "discount_id": item.discount_id,
                    "product_image": get_order_item_image(item.product_id),
                    "product_name": Product.query.get(item.product_id).name,
                    "price": item.price
                } for item in order.order_items
            ]
        })
    return jsonify(result), 200

