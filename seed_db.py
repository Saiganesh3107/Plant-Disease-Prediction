# seed_db.py -- creates a test user and optional sample predictions
import os
from db import get_conn
from auth_utils import hash_password
import shutil

def create_user(username='testuser', email='test@example.com', password='testpass'):
    conn = get_conn()
    cur = conn.cursor()
    try:
        pw_hash = hash_password(password)
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s,%s,%s)",
                    (username, email, pw_hash))
        conn.commit()
        print('Created user:', username)
    except Exception as e:
        conn.rollback()
        print('Could not create user (maybe already exists):', e)
    finally:
        cur.close()
        conn.close()

def add_sample_prediction(username='testuser'):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    if not row:
        print('User not found:', username)
        cur.close()
        conn.close()
        return
    user_id = row['id']
    # copy a placeholder image into uploads if not exists
    uploads_dir = 'uploads'
    os.makedirs(uploads_dir, exist_ok=True)
    sample_src = os.path.join('static','saliency')
    sample_dst = os.path.join(uploads_dir, 'sample_leaf.jpg')
    # create a tiny placeholder image
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGB', (224,224), (200,240,200))
    d = ImageDraw.Draw(im)
    d.text((10,100), 'Sample Leaf', fill=(0,40,0))
    im.save(sample_dst)
    try:
        cur.execute("""INSERT INTO predictions (user_id, image_path, label, confidence, saliency_path)
                       VALUES (%s,%s,%s,%s,%s)""", (user_id, sample_dst, 'Sample_Disease', 0.85, None))
        conn.commit()
        print('Inserted sample prediction for', username)
    except Exception as e:
        conn.rollback()
        print('Could not insert sample prediction:', e)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    create_user()
    add_sample_prediction()
