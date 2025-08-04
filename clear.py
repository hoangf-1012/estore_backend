import os
import shutil
from app.extensions import db
from app import create_app

app = create_app()

def clearall():
    # Xóa thư mục __pycache__
    for root, dirs, file in os.walk(".", topdown=False):
        for name in dirs:
            if name == "__pycache__":
                shutil.rmtree(os.path.join(root, name))
                print(f"Đã xóa: {os.path.join(root, name)}")
            if name == "instance":
                shutil.rmtree(os.path.join(root, name))
                print(f"Đã xóa: {os.path.join(root, name)}")
            if name == "product":
                shutil.rmtree(os.path.join(root, name))
                print(f"Đã xóa: {os.path.join(root, name)}")
            if name == "user":
                shutil.rmtree(os.path.join(root, name))
                print(f"Đã xóa: {os.path.join(root, name)}")

if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        print("Database cleared successfully!")
    clearall()