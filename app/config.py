import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///estore.db")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") 
    JWT_BLACKLIST_ENABLED = True
    JWT_ALGORITHMS = ["HS256"]
    JWT_HEADER_TYPE= "Bearer"
    JWT_TOKEN_LOCATION= ["headers"]
    JWT_VERIFY_SUB = False
    JWT_ACESS_TOKEN_EXPIRES = timedelta(days=7)

    UPLOAD_FOLDER = UPLOAD_FOLDER
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
 

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = MAIL_USERNAME
