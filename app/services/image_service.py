import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

def generate_unique_filename(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

def save_image(file, folder="uploads"):
    if not allowed_file(file.filename):
        return None, "Invalid file format"

    filename = generate_unique_filename(file.filename)
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], folder, filename)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)

    return f"/{folder}/{filename}", None

def delete_image(image_path):
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(image_path))
    if os.path.exists(file_path):
        os.remove(file_path)
