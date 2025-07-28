from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import User
from functools import wraps

def role_required(*allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            identity = get_jwt_identity()
            
            if not identity or "role" not in identity:
                return jsonify({"message": "Unauthorized"}), 403
            
            user_role = identity["role"]  
            if user_role not in [role.value for role in allowed_roles]:  
                return jsonify({"message": "Forbidden: Insufficient permissions"}), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper

def active_required():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            identity = get_jwt_identity()
            current_user = User.query.filter_by(id=identity["id"] ).first()
            if not current_user or not current_user.is_active:
                return jsonify({"message": "your account has been deactivated!"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator