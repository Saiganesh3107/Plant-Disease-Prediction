import os

def ensure_dirs():
    for d in ['uploads','static/saliency','models']:
        os.makedirs(d, exist_ok=True)

if __name__ == '__main__':
    ensure_dirs()
