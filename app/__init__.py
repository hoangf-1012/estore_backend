from flask import Flask
from app.config import Config
from app.extensions import db, jwt, mail
from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.product import product_bp
from app.routes.category import category_bp
from app.routes.review import review_bp
from app.routes.image import image_bp
from app.routes.order import order_bp
from app.routes.discount import discount_bp
from app.routes.cart import cart_bp
from app.models import User, UserRole
from werkzeug.security import generate_password_hash
from flasgger import Swagger
import yaml

def create_admin():
    admin_email = "truyenh527@gmail.com"
    admin_username = "administrator"

    if not User.query.filter_by(email=admin_email).first():
        hashed_password = generate_password_hash("admin123")
        admin = User(
            username=admin_username,
            email=admin_email,
            password_hash=hashed_password,
            role=UserRole.admin,
            full_name="Administrator",
            phone_number="0000000000"
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin account created: truyenh527@gmail.com / admin123")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)


    with open("docs/swagger.yaml", "r",encoding="utf-8") as file:
        swagger_template = yaml.safe_load(file)

    Swagger(app, template=swagger_template)

    with app.app_context():
        db.create_all()
        create_admin()
        print("Database created successfully!")

    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(category_bp, url_prefix="/api/category")
    app.register_blueprint(product_bp, url_prefix="/api/product")
    app.register_blueprint(review_bp, url_prefix="/api/review")
    app.register_blueprint(image_bp, url_prefix="/api/image")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(order_bp, url_prefix="/api/order")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(discount_bp, url_prefix="/api/discount")

    return app

