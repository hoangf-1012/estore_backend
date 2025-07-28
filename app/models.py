from app.extensions import db
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import random

class UserRole(enum.Enum):
    admin = "Admin"
    staff = "Staff"
    customer = "Customer"

class Gender(enum.Enum):
    male = "Male"
    female = "Female"
    other = "Other"

class OrderStatus(enum.Enum):
    pending = "Pending"
    processing = "Processing"
    shipping = "Shipping"
    completed = "Completed"
    canceled = "Canceled"
    returned = "Returned"

def generate_default_username():
    return f"user_{random.randint(100000000000, 999999999999)}"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=False, default=generate_default_username)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.Enum(Gender), nullable=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.customer)
    is_active = db.Column(db.Boolean, default=True)
    verification_code = db.Column(db.String(6), nullable=True)
    verification_code_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    reviews = relationship("Review", backref="user", cascade="all, delete-orphan", passive_deletes=True)
    cart_items = relationship("CartItem", backref="user", cascade="all, delete-orphan", passive_deletes=True)

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    street_address = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(100), nullable=True)
    province = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=True)
    is_default = db.Column(db.Boolean, default=False)

    user = relationship("User", back_populates="addresses")

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("category.id", ondelete="SET NULL"), nullable=True)

    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan", passive_deletes=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    material = db.Column(db.String(100), nullable=True)
    origin = db.Column(db.String(100), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    discount = db.Column(db.Integer, nullable=True, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id", ondelete="CASCADE"), nullable=False)

    category = relationship("Category", back_populates="products")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan", passive_deletes=True)
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan", passive_deletes=True)
    order_items = relationship("OrderItem", back_populates="product", passive_deletes=True)
    cart_items = relationship("CartItem", backref="product", passive_deletes=True)

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    product = relationship("Product", back_populates="images")

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.pending)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", passive_deletes=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    discount_id = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Float, nullable=False)

    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="reviews")

class Discount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    release_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)
    max_users = db.Column(db.Integer, nullable=True)
    minimum_order_value = db.Column(db.Float, nullable=True)

    users_collected = relationship('UserDiscount', backref='discount', cascade="all, delete-orphan", passive_deletes=True)

    def is_valid(self):
        return self.release_date <= datetime.utcnow() <= self.expiration_date and \
               (self.max_users is None or len(self.users_collected) < self.max_users)

class UserDiscount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    discount_id = db.Column(db.Integer, db.ForeignKey('discount.id', ondelete="CASCADE"), nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)

    def use_discount(self):
        if not self.is_used:
            self.is_used = True
            db.session.commit()
            return True
        return False
