from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils.security import role_required, active_required
from app.extensions import db
from app.models import Category, UserRole

category_bp = Blueprint("category", __name__)

# Lấy danh sách danh mục
@category_bp.route("/categories", methods=["GET"])
def get_categories():
    parent_id = request.args.get("parent_id") 
    
    query = Category.query
    if parent_id:
        query = query.filter_by(parent_id=parent_id)

    categories = query.all()
    result = [
        {
            "id": category.id,
            "name": category.name,
            "parent_id": category.parent_id
        }
        for category in categories
    ]
    return jsonify(result), 200


# thêm danh mục (Chỉ Admin)
@category_bp.route("/add-category", methods=["POST"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def add_category():
    data = request.get_json()
    name = data.get("name")
    parent_id = data.get("parent_id")


    if not name:
        return jsonify({"message": "Category name is required"}), 400

    if Category.query.filter_by(name=name).first():
        return jsonify({"message": "Category already exists"}), 400
    
    if parent_id and not Category.query.get(parent_id):
        return jsonify({"message": "Parent category does not exist"}), 400

    if not parent_id:
        parent_id = None

    new_category = Category(name=name, parent_id=parent_id)
    db.session.add(new_category)
    db.session.commit()

    return jsonify({"message": "Category added successfully"}), 201


# Cập nhật danh mục (Chỉ Admin)
@category_bp.route("/update-category/<int:category_id>", methods=["PUT"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def update_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "Category not found"}), 404

    data = request.get_json()


    name = data.get("name", category.name)
    parent_id = data.get("parent_id", category.parent_id)

    if not name and not parent_id:
        return jsonify({"message": "notthing to update"}), 304

    category.name = name
    category.parent_id = parent_id
    db.session.commit()

    return jsonify({"message": "Category updated successfully"}), 200

def set_null_parent_id(category_id):
    category = Category.query.get(category_id)
    category.parent_id = None
    db.session.commit()


# Xóa danh mục (Chỉ Admin)
@category_bp.route("/delete-category/<int:category_id>", methods=["DELETE"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "Category not found"}), 404

    if category.subcategories:
        for subcategory in category.subcategories:
            try:
                set_null_parent_id(subcategory.id)
            except Exception:
                pass

    if category.products:
        return jsonify({"message": "Cannot delete category with products"}), 400

    db.session.delete(category)
    db.session.commit()

    return jsonify({"message": "Category deleted successfully"}), 200
