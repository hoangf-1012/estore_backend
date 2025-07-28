from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils.security import role_required
from app.services.product_service import get_product_with_details, set_default_image, save_product_image
from app.services.image_service import delete_image
from app.extensions import db
from app.utils.security import active_required
from app.models import Category, Product, ProductImage, UserRole, Review

product_bp = Blueprint("product", __name__)


# Lấy chi tiết sản phẩm kèm rating trung bình
@product_bp.route("/product/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product_data = get_product_with_details(product_id)
    if not product_data:
        return jsonify({"message": "Product not found"}), 404
    return jsonify(product_data), 200

# Thêm sản phẩm mới (Chỉ Admin)
@product_bp.route("/add-product", methods=["POST"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def add_product():
    name = request.form.get("name")
    description = request.form.get("description")
    price = request.form.get("price", type=float)
    stock = request.form.get("stock", 0, type=int)
    material = request.form.get("material")
    origin = request.form.get("origin")
    brand = request.form.get("brand")
    discount = request.form.get("discount", 0, type=int)
    category_id = request.form.get("category_id", type=int)

    if not name or price is None or category_id is None:
        return jsonify({"message": "Missing required fields"}), 400
    
    new_product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        material=material,
        origin=origin,
        brand=brand,
        discount=discount,
        category_id=category_id
    )
    db.session.add(new_product)
    db.session.commit()

    default_image_url = None
    if "default_image" in request.files:
        file = request.files["default_image"]
        if file.filename:
            default_image_url, error = save_product_image(new_product.id, file)
            if error:
                print(error)
                return jsonify({
                    "message": "Product added successfully with error upload image",
                    "product_id": new_product.id,
                }), 207
            set_default_image(new_product.id, default_image_url)
    sub_images_urls = []
    if "sub_images" in request.files:
        files = request.files.getlist("sub_images")
        has_error = False
        for file in files:
            if file.filename:
                image_url, error = save_product_image(new_product.id, file)
                if error:
                    has_error=True
                else:
                    sub_images_urls.append(image_url)
        if has_error:
            return jsonify({
                "message": "Product added successfully with error upload image",
                "product_id": new_product.id,
                "default_image": default_image_url,
                "sub_image": sub_images_urls
            }), 207


    return jsonify({
        "message": "Product added successfully",
        "product_id": new_product.id,
        "default_image": default_image_url,
        "sub_image": sub_images_urls
    }), 201

# Thêm hình ảnh cho sản phẩm (Chỉ Admin)
@product_bp.route("/upload-image/<int:product_id>", methods=["POST"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def upload_product_image(product_id):
    is_default = request.form.get("is_default", "false").lower() in ["true", "1"]
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    if "image" in request.files:
        file = request.files["image"]
        if file.filename:
            image_url, error = save_product_image(product_id, file)
            if error:
                return jsonify({
                    "error": "Unable to load saved image",
                    "product_id": product_id,
                }), 400
            if is_default:
                new_default_image = ProductImage.query.filter_by(image_url=image_url).first()
                if not new_default_image:
                    return jsonify({"error": "Saved image not found"}), 404
                current_default_image = ProductImage.query.filter_by(product_id=new_default_image.product_id, is_default=True).first()
                if current_default_image:
                    current_default_image.is_default = False
                new_default_image.is_default = True
                db.session.commit()
            return jsonify({    
                "message": "Images uploaded successfully",
                "image_uploaded_url": image_url 
            }), 201
    else:
        return jsonify({"message": "No file part"}), 400

# Xóa hình ảnh sản phẩm (Chỉ Admin)
@product_bp.route("/delete-image/<int:image_id>", methods=["DELETE"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def delete_product_image_api(image_id):
    image = ProductImage.query.get(image_id)
    if not image:
        return jsonify({"message": "Image not found"}), 404
    if image.is_default:
        return jsonify({"message": "Cannot delete default image"}), 400
    delete_image(image.image_url)
    db.session.delete(image)
    db.session.commit()

    return jsonify({"message": "Image deleted successfully"}), 200


# Cập nhật thông tin sản phẩm (Chỉ Admin)
@product_bp.route("/update-product/<int:product_id>", methods=["PUT"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    data = request.get_json()
    product.name = data.get("name", product.name)
    product.description = data.get("description", product.description)
    product.price = data.get("price", product.price)
    product.stock = data.get("stock", product.stock)
    product.material = data.get("material", product.material)
    product.origin = data.get("origin", product.origin)
    product.brand = data.get("brand", product.brand)
    product.category_id = data.get("category_id", product.category_id)

    db.session.commit()

    if "default_image_url" in data:
        set_default_image(product.id, data["default_image_url"])

    return jsonify({"message": "Product updated successfully"}), 200


# Xóa sản phẩm và hình ảnh (Chỉ Admin)
@product_bp.route("/delete-product/<int:product_id>", methods=["DELETE"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def delete_product_api(product_id):

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    
    images = ProductImage.query.filter_by(product_id=product_id).all()

    if images:
        for image in images:
            delete_image(image.image_url)
            db.session.delete(image)

    db.session.delete(product)
    db.session.commit() 

    return jsonify({"message": "Product deleted successfully"}), 200



# Lấy danh sách sản phẩm 
@product_bp.route("/products", methods=["GET"])
def get_products_by_category():
    category_id = request.args.get("category_id", type=int)
    
    if not category_id:
        products = Product.query.all()
        result = [get_product_with_details(prod.id) for prod in products]
        return jsonify(result), 200

    def get_subcategories(category):
        subcategories = [sub.id for sub in category.subcategories]
        for sub in category.subcategories:
            subcategories.extend(get_subcategories(sub))
        return subcategories

    root_category = Category.query.get(category_id)
    if not root_category:
        return jsonify({"error": "Category not found"}), 404

    category_ids = [root_category.id] + get_subcategories(root_category)

    products = Product.query.filter(Product.category_id.in_(category_ids)).all()

    result = [get_product_with_details(product.id) for product in products]

    return jsonify(result), 200


#đặt hình ảnh sản phẩm mặc định
@product_bp.route("/set-default-image/<int:image_id>", methods=["PUT"])
@jwt_required()
@active_required()
@role_required(UserRole.admin, UserRole.staff)
def set_default_image_product_api(image_id):
    new_default_image = ProductImage.query.get(image_id)
    if not new_default_image:
        return jsonify({"error": "image not found"}), 404
    current_default_image = ProductImage.query.filter_by(product_id=new_default_image.product_id, is_default=True).first()
    if current_default_image:
        current_default_image.is_default = False
    new_default_image.is_default = True
    db.session.commit()
    return jsonify({"message": "Set default image successfully"}), 200