from datetime import datetime
import random
import string
from flask_mail import Message
from app.extensions import mail
import re

def is_valid_email(email: str) -> bool:
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(email_regex, email))

# Tạo mã xác nhận ngẫu nhiên
def generate_verification_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Gửi mã xác nhận đến email
def send_verification_code(email, code, purpose="verification"):
    subject = "Your Verification Code"
    if purpose == "password_reset":
        subject = "Password Reset Code"
    elif purpose == "email_change":
        subject = "Email Change Confirmation Code"

    msg = Message(subject, recipients=[email])
    msg.body = f"Your verification code is: {code}. It will expire in 10 minutes."
    mail.send(msg)

# Kiểm tra mã xác nhận còn hạn sử dụng không
def is_verification_code_valid(user, code):
    return (
        user.verification_code == code and 
        user.verification_code_expires_at and 
        datetime.utcnow() < user.verification_code_expires_at
    )

def send_notification(email, subject, body):
    msg = Message(subject, recipients=[email])
    msg.body = body
    mail.send(msg)