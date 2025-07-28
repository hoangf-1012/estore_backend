from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.security import role_required, active_required
from app.extensions import db
from app.models import Order, OrderItem, OrderStatus, Review, Product, UserRole

review_bp = Blueprint("review", __name__)


def has_purchased_product(user_id, product_id):
    return db.session.query(OrderItem.id).join(Order).filter(
        OrderItem.product_id == product_id,
        OrderItem.order_id == Order.id,
        Order.user_id == user_id,
        Order.status.in_([OrderStatus.completed, OrderStatus.shipping])
    ).first() is not None


# Lấy danh sách đánh giá của sản phẩm
@review_bp.route("/product/<int:product_id>", methods=["GET"])
def get_reviews(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    reviews = Review.query.filter_by(product_id=product_id).all()
    result = [
        {
            "id": rev.id,
            "user": rev.user.full_name,
            "rating": rev.rating,
            "comment": rev.comment,
            "created_at": rev.created_at
        }
        for rev in reviews
    ]
    return jsonify(result), 200

# Lấy danh sách đánh giá của người dùng
@review_bp.route("/user/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user_reviews(user_id):
    identity = get_jwt_identity()
    
    # Chỉ Admin mới có thể xem review của user khác
    if identity["role"] != UserRole.admin.value and identity["id"] != user_id:
        return jsonify({"message": "Forbidden: You can only view your own reviews"}), 403

    reviews = Review.query.filter_by(user_id=user_id).all()
    result = [
        {
            "id": rev.id,
            "product_id": rev.product_id,
            "product_name": rev.product.name,
            "rating": rev.rating,
            "comment": rev.comment,
            "created_at": rev.created_at
        }
        for rev in reviews
    ]

    return jsonify(result), 200

# Thêm đánh giá sản phẩm (Chỉ Customer đã mua hàng)
@review_bp.route("/add-review/<int:product_id>", methods=["POST"])
@jwt_required()
@active_required()
def add_review(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    identity = get_jwt_identity()
    user_id = identity["id"]

    if not has_purchased_product(user_id, product_id):
        return jsonify({"message": "You can only review products you have purchased"}), 403

    data = request.get_json()
    rating = data.get("rating")
    comment = data.get("comment", "")

    if not (1 <= rating <= 5):
        return jsonify({"message": "Rating must be between 1 and 5"}), 400

    new_review = Review(user_id=user_id, product_id=product_id, rating=rating, comment=comment)
    db.session.add(new_review)
    db.session.commit()

    return jsonify({"message": "Review added successfully"}), 201

# Sửa đánh giá (Chỉ người đã viết)
@review_bp.route("/update/<int:review_id>", methods=["PUT"])
@jwt_required()
@active_required()
def update_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"message": "Review not found"}), 404

    identity = get_jwt_identity()
    if review.user_id != identity["id"]:
        return jsonify({"message": "Forbidden: You can only edit your own review"}), 403

    data = request.get_json()
    review.rating = data.get("rating", review.rating)
    review.comment = data.get("comment", review.comment)
    db.session.commit()

    return jsonify({"message": "Review updated successfully"}), 200


# Xóa đánh giá (Chỉ người đã viết hoặc Admin)
@review_bp.route("/delete/<int:review_id>", methods=["DELETE"])
@jwt_required()
@active_required()
def delete_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"message": "Review not found"}), 404

    identity = get_jwt_identity()
    if review.user_id != identity["id"] and identity["role"] != UserRole.admin.value:
        return jsonify({"message": "Forbidden: You can only delete your own review or be an Admin"}), 403

    db.session.delete(review)
    db.session.commit()

    return jsonify({"message": "Review deleted successfully"}), 200


# Lấy toàn bộ đánh giá (Chỉ Admin)
@review_bp.route("/reviews", methods=["GET"])
@jwt_required()
@role_required(UserRole.admin)
def get_all_reviews():
    product_id = request.args.get("product_id", type=int)
    user_id = request.args.get("user_id", type=int)
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)

    query = Review.query

    if product_id:
        query = query.filter_by(product_id=product_id)
    if user_id:
        query = query.filter_by(user_id=user_id)

    reviews = query.paginate(page=page, per_page=limit, error_out=False)

    result = [
        {
            "id": rev.id,
            "product_id": rev.product_id,
            "product_name": rev.product.name,
            "user_id": rev.user_id,
            "user_name": rev.user.full_name,
            "rating": rev.rating,
            "comment": rev.comment,
            "created_at": rev.created_at
        }
        for rev in reviews.items
    ]

    return jsonify({
        "total": reviews.total,
        "page": reviews.page,
        "per_page": reviews.per_page,
        "reviews": result
    }), 200