import os
from io import BytesIO
from datetime import datetime

from flask import Flask, request, jsonify, render_template, send_file, session, redirect
from werkzeug.utils import secure_filename

from model_loader import load_models, predict_image
from db import get_conn  # your DB helper

# ReportLab for PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from PIL import Image

app = Flask(__name__)
app.secret_key = "plant_ai_secret"

UPLOAD_FOLDER = "static/uploads"
SALIENCY_FOLDER = "static/saliency"
CLASS_FILE = "classes.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SALIENCY_FOLDER, exist_ok=True)
os.makedirs("models", exist_ok=True)

# Load model (adjust your path / model name as needed)
models = load_models({'base': 'models/best_vit.pth'})

# Optional: require login for protected routes
@app.before_request
def require_login():
    allowed_prefixes = ['/login', '/register', '/static/', '/favicon.ico', '/download_report']
    for p in allowed_prefixes:
        if request.path.startswith(p):
            return
    if 'user_id' not in session:
        return redirect('/login')


@app.route('/')
def index():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # keep your existing login logic
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users1 WHERE username=%s AND password_hash=%s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/home')
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


@app.route('/home')
def home():
    return render_template('plant_disease_ui.html', username=session.get('username'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone_number')

        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users1 (firstname, lastname, username, password_hash, phone_number, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (firstname, lastname, username, password, phone))
            conn.commit()
            cur.close()
            conn.close()
            return redirect('/login')
        except Exception as e:
            print("⚠️ Registration failed:", e)
            return render_template('register.html', error="Registration failed. Try again.")

    return render_template('register.html')



@app.route('/history')
def history_page():
    return render_template('history.html')


@app.route('/api/history')
def api_history():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id, image_path, leaf, disease, confidence, severity, saliency_path, created_at
            FROM predictions
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (session['user_id'],))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # convert to web paths
        for r in rows:
            if r.get('image_path'):
                r['image_path'] = '/' + r['image_path'].replace("\\", "/")
            if r.get('saliency_path'):
                r['saliency_path'] = '/' + r['saliency_path'].replace("\\", "/")
        return jsonify({"history": rows})
    except Exception as e:
        print("⚠️ Error fetching history:", e)
        return jsonify({"error": "Database error", "details": str(e)}), 500


@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    result = predict_image(models['base'], filepath, CLASS_FILE, SALIENCY_FOLDER)

    # Save prediction to DB (leaf instead of fruit)
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
               INSERT INTO predictions (user_id, image_path, leaf, disease, confidence, severity, saliency_path, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session['user_id'],
            filepath,
            result.get('leaf'),
            result.get('disease'),
            result.get('confidence'),
            result.get('severity'),
            result.get('saliency'),
            datetime.now()
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("⚠️ Database insert failed:", e)

    # Return prediction + server-stored image path so frontend can ask server to include it in the PDF
    return jsonify({
        "leaf": result.get('leaf') or result.get('fruit') or 'Unknown',
        "disease": result.get('disease'),
        "confidence": result.get('confidence'),
        "severity": result.get('severity'),
        "saliency": "/" + result.get('saliency') if result.get('saliency') else None,
        "image_path": "/" + filepath.replace("\\", "/")
    })


# ---------------- PDF generation for current prediction ----------------
@app.route('/download_report', methods=['POST'])
def download_report():
    """
    Expects JSON body with keys:
    {
      "leaf": "Corn_(maize)",
      "disease": "Northern_Leaf_Blight",
      "confidence": 92.3,
      "severity": 34.2,
      "image_path": "/static/uploads/abc.jpg",
      "saliency": "/static/saliency/abc_saliency.png"   (optional)
    }
    Returns generated PDF file.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    # Build PDF in-memory
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("Plant AI — Prediction Report", styles['Title']))
        story.append(Spacer(1, 6))

        info_data = [
            ['Leaf', data.get('leaf', 'Unknown')],
            ['Disease', data.get('disease', 'Unknown')],
            ['Confidence', f"{data.get('confidence', 0):.2f}%"],
            ['Severity', f"{data.get('severity', 0):.2f}%"],
            ['Generated at', datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")]
        ]
        t = Table(info_data, hAlign='LEFT', colWidths=[80*mm, 90*mm])
        t.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.25, colors.gray),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.gray),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        def add_image(path, label):
            if not path:
                return
            local_path = path.lstrip('/')
            if not os.path.exists(local_path):
                # try as-is
                local_path = path
            if not os.path.exists(local_path):
                story.append(Paragraph(f"{label}: (image not found)", styles['Normal']))
                story.append(Spacer(1, 6))
                return
            try:
                img = RLImage(local_path)
                img._restrictSize(160*mm, 120*mm)
                story.append(Paragraph(label, styles['Heading5']))
                story.append(img)
                story.append(Spacer(1, 8))
            except Exception as e:
                story.append(Paragraph(f"{label}: (error adding image)", styles['Normal']))
                story.append(Spacer(1, 6))

        # add uploaded image and saliency if present
        add_image(data.get('image_path'), "Uploaded Leaf Image")
        add_image(data.get('saliency'), "Saliency / Heatmap")

        doc.build(story)
        buffer.seek(0)
        filename = f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{(data.get('leaf') or 'leaf')}.pdf"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

    except Exception as e:
        print("❌ Error generating PDF:", str(e))
        return jsonify({"error": "PDF generation failed", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
