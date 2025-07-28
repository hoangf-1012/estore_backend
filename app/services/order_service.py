from app.models import Discount, UserDiscount, Product, CartItem, ProductImage
from datetime import datetime
from app.extensions import db
def apply_discount(user_id, discount_id, price):

    discount = Discount.query.filter_by(id=discount_id).first()
    
    if not discount:
        return None, "Invalid discount code"
    
    if discount.expiration_date < datetime.utcnow():
        return None, "Discount code has expired"

    if discount.release_date > datetime.utcnow():
        return None, "Discount code is not active yet"
    
    if discount.minimum_order_value and price < discount.minimum_order_value:
        return None, f"Minimum order value to use this discount is {discount.minimum_order_value}"

    user_discount = UserDiscount.query.filter_by(user_id=user_id, discount_id=discount.id, is_used=False).first()
    if not user_discount:
        return None, "You haven't collected or already used this discount"
    user_discount.is_used = True
    db.session.commit()

    discount_amount = price * (discount.discount_percent / 100)
    return discount_amount, None


def validate_item_discount(discount_id, user_id, product_price, quantity):
    if not discount_id:
        return None, None

    discount = Discount.query.get(discount_id)
    current_time = datetime.utcnow()

    if not discount:
        return None, "Discount not found"
    if discount.release_date > current_time or discount.expiration_date < current_time:
        return None, "Discount is not active"
    user_discount = UserDiscount.query.filter_by(user_id=user_id, discount_id=discount.id, is_used=False).first()
    if not user_discount:
        return None, "User has not collected this discount or it has already been used"
    if product_price * quantity < discount.minimum_order_value:
        return None, "Order item does not meet minimum value for discount"

    user_discount.is_used = True
    db.session.commit()
    return discount, None


def calculate_order_items_total(order_items_data, user_id):
    order_items = []
    total_price = 0


    for item_data in order_items_data:
        product_id = item_data.get("product_id")
        quantity = item_data.get("quantity", 1)
        discount_id = item_data.get("discount_id")

        if not product_id or quantity <= 0:
            return None, None, f"Invalid product_id or quantity in item: {item_data}"

        product = Product.query.get(product_id)
        if not product:
            return None, None, f"Product with id {product_id} not found"
        
        if quantity > product.stock:
            return None, None, f"Not enough stock for product {product_id}. Available: {product.stock}, Requested: {quantity}"

        original_price = product.price * (1 - product.discount / 100)
        final_price = original_price

        discount = None
        if discount_id:
            discount, error = validate_item_discount(discount_id, user_id, original_price, quantity)
            if error:
                return None, None, f"Discount error for product {product_id}: {error}"
            final_price = (original_price * quantity) * (1 - discount.discount_percent / 100)

        total_price += final_price

        order_items.append({
            "product_id": product_id,
            "quantity": quantity,
            "price": final_price,
            "discount_id": discount.id if discount else None
        })

    return order_items, total_price, None

def get_order_item_image(product_id):
    image = ProductImage.query.filter_by(product_id= product_id,is_default=True).first()
    if not image:
        return None
    return image.image_url
