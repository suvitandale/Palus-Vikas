# app.py (updated with admin dashboard)
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime
import random
import string
import functools
import io
import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static', template_folder='templates')

# IMPORTANT: change this in production (or set environment var FLASK_SECRET)
app.secret_key = os.environ.get('FLASK_SECRET', 'change_this_secret_in_production')



# Choices mapping for subcategories (same as before)
CHOICES = {
    "पाणीपुरवठा": [
        "पाणी कमी येणे", "पाणी न येणे", "गळकी पाइपलाइन", "दूषित पाणी", "चुकीचे बिल", "नवीन कनेक्शन"
    ],
    "वीज समस्या": [
        "वीज जात आहे", "कमी-जास्त व्होल्टेज", "स्ट्रीट लाईट बंद", "तुटलेले वीजतार", "मीटर तक्रार", "नवीन मीटर"
    ],
    "कचरा व्यवस्थापन": [
        "कचरा वेळेवर न उचलणे", "गटार तुंबणे", "रस्त्यावर कचरा", "ड्रेनेज लाईन तुटणे", "नाली साफसफाई", "कचरा कुंडी भरलेली"
    ],
    "रस्ते / ड्रेनेज": [
        "खड्डेमय रस्ता", "तुटलेली गटार पत्रे", "पाणी साचणे", "रस्ता खराब", "अपूर्ण काम", "फुटपाथ समस्या"
    ]
}

DB_PATH = 'palus_vikas.db'

def gen_ticket_id():
    date_str = datetime.utcnow().strftime("%Y%m%d")
    rnd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"PV-{date_str}-{rnd}"

def insert_complaint(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    INSERT INTO complaints (ticket_id, main_category, sub_category, prabhag, address, contact, email, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['ticket_id'],
        data['main_category'],
        data['sub_category'],
        data.get('prabhag'),
        data.get('address'),
        data.get('contact'),
        data.get('email'),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

# ---------- Admin auth helpers ----------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.path))
        return view(*args, **kwargs)
    return wrapped_view

# ---------- Public routes (unchanged) ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/categories')
def categories():
    categories_list = [
        {"key":"पाणीपुरवठा", "label":"💧 पाणीपुरवठा"},
        {"key":"वीज समस्या", "label":"⚡ वीज समस्या"},
        {"key":"कचरा व्यवस्थापन", "label":"🗑️ कचरा व्यवस्थापन"},
        {"key":"रस्ते / ड्रेनेज", "label":"🛣️ रस्ते / ड्रेनेज"},
    ]
    return render_template('categories.html', categories=categories_list)

@app.route('/choices')
def choices():
    cat = request.args.get('category')
    items = CHOICES.get(cat, [])
    return jsonify(items)

@app.route('/complaint/<category>')
def complaint_form(category):
    return render_template('complaint.html', main_category=category)

@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    data = request.json
    required = ['main_category', 'sub_category', 'prabhag', 'address', 'contact']
    for r in required:
        if not data.get(r):
            return jsonify({"status":"error", "message": f"Missing {r}"}), 400

    ticket_id = gen_ticket_id()
    data['ticket_id'] = ticket_id
    try:
        insert_complaint(data)
    except Exception as e:
        return jsonify({"status":"error", "message": str(e)}), 500

    return jsonify({"status":"ok", "ticket_id": ticket_id})

# ---------- Admin routes ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row['password_hash'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            next_url = request.args.get('next') or url_for('admin_dashboard')
            return redirect(next_url)
        else:
            flash("Invalid username or password", "error")
            return render_template('admin_login.html')
    else:
        return render_template('admin_login.html')

@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash("Logged out", "info")
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # optional filters via query params
    category = request.args.get('category', '')
    prabhag = request.args.get('prabhag', '')
    search = request.args.get('search', '')

    query = "SELECT * FROM complaints WHERE 1=1"
    params = []
    if category:
        query += " AND main_category = ?"
        params.append(category)
    if prabhag:
        query += " AND prabhag LIKE ?"
        params.append(f"%{prabhag}%")
    if search:
        query += " AND (ticket_id LIKE ? OR address LIKE ? OR contact LIKE ? OR email LIKE ? OR sub_category LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s, s])

    query += " ORDER BY created_at DESC LIMIT 1000"  # limit to 1000 for safety

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    # categories for filter UI
    cat_list = [
        "पाणीपुरवठा", "वीज समस्या", "कचरा व्यवस्थापन", "रस्ते / ड्रेनेज"
    ]
    return render_template('admin_dashboard.html', complaints=rows, categories=cat_list,
                           filter_category=category, filter_prabhag=prabhag, filter_search=search)

@app.route('/admin/delete/<int:complaint_id>', methods=['POST'])
@admin_required
def admin_delete(complaint_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM complaints WHERE id = ?", (complaint_id,))
    conn.commit()
    conn.close()
    flash("Complaint deleted.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/export', methods=['GET'])
@admin_required
def admin_export():
    # Export filtered results as CSV (same filter logic as dashboard)
    category = request.args.get('category', '')
    prabhag = request.args.get('prabhag', '')
    search = request.args.get('search', '')

    query = "SELECT * FROM complaints WHERE 1=1"
    params = []
    if category:
        query += " AND main_category = ?"
        params.append(category)
    if prabhag:
        query += " AND prabhag LIKE ?"
        params.append(f"%{prabhag}%")
    if search:
        query += " AND (ticket_id LIKE ? OR address LIKE ? OR contact LIKE ? OR email LIKE ? OR sub_category LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s, s])

    query += " ORDER BY created_at DESC"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    # Create CSV in-memory
    output = io.StringIO()
    writer = csv.writer(output)
    header = ['id','ticket_id','main_category','sub_category','prabhag','address','contact','email','created_at']
    writer.writerow(header)
    for r in rows:
        writer.writerow([r['id'], r['ticket_id'], r['main_category'], r['sub_category'],
                         r['prabhag'], r['address'], r['contact'], r['email'], r['created_at']])
    output.seek(0)

    # send as attachment
    filename = f"complaints_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

# ---------- run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host='0.0.0.0', debug=True, port=port)
