import os
from flask import Blueprint, request, send_from_directory, current_app, jsonify
from app.models import User

image_bp = Blueprint("image", __name__)

@image_bp.route("/get-image", methods=["GET"])
def get_image():
    image_path = request.args.get("path")

    if not image_path:
        return jsonify({"message": "Missing image path"}), 400


    full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], image_path.lstrip("/"))
    if not os.path.exists(full_path):
        return jsonify({"message": "Image not found"}), 404

    return send_from_directory(current_app.config["UPLOAD_FOLDER"], image_path.lstrip("/"))

@image_bp.route("/get-user-avatar/<int:user_id>", methods=["GET"])
def get_user_avatar(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    image_path = user.avatar_url
    if not image_path:
        return jsonify({"message": "User has no avatar"}), 404

    if not image_path:
        return jsonify({"message": "Missing image path"}), 400

    full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], image_path.lstrip("/"))
    if not os.path.exists(full_path):
        return jsonify({"message": "Image not found"}), 404

    return send_from_directory(current_app.config["UPLOAD_FOLDER"], image_path.lstrip("/"))
 