from sqlalchemy import func
from app.extensions import db
from app.models import Product, ProductImage, Review, OrderItem, Order, OrderStatus
from app.services.image_service import save_image, delete_image

def get_product_with_details(product_id):
    product = Product.query.get(product_id)
    if not product:
        return None

    images = [
        {"id": img.id, "url": img.image_url, "is_default": img.is_default} 
        for img in product.images
    ]


    avg_rating = db.session.query(func.coalesce(func.avg(Review.rating), 0)).filter(Review.product_id == product.id).scalar()
    rounded_rating = round(avg_rating) 

    sold_quantity = db.session.query(func.coalesce(func.sum(OrderItem.quantity), 0)).join(Order).filter(
        OrderItem.product_id == product.id, 
        Order.status == OrderStatus.completed
    ).scalar()

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "material": product.material,
        "origin": product.origin,
        "brand": product.brand,
        "category_id": product.category_id,
        "rate": int(rounded_rating), 
        "sold": sold_quantity,
        "discount": product.discount,
        "images": images
    }

def set_default_image(product_id, image_url):
    ProductImage.query.filter_by(product_id=product_id).update({"is_default": False})


    existing_image = ProductImage.query.filter_by(product_id=product_id, image_url=image_url).first()

    if existing_image:
        existing_image.is_default = True 
    else:
        new_image = ProductImage(product_id=product_id, image_url=image_url, is_default=True)
        db.session.add(new_image)

    db.session.commit()


def save_product_image(product_id, file):
    image_url, error = save_image(file, folder="uploads/product")
    if error:
        return None, error

    image = ProductImage(product_id=product_id, image_url=image_url)
    db.session.add(image)
    db.session.commit()
    return image.image_url, None
