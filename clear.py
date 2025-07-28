import os
import shutil

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
            if name == "migrations":
                shutil.rmtree(os.path.join(root, name))
                print(f"Đã xóa: {os.path.join(root, name)}")

if __name__ == "__main__":
    clearall()