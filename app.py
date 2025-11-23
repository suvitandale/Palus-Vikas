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

SCHEMES = {
    "घरकुल आवास योजना": ["अर्ज", "स्थिती तपासा", "डाउनलोड फॉर्म"],
    "रमाई आवास योजना": ["अर्ज", "स्थिती तपासा", "डाउनलोड फॉर्म"],
    "पीएम स्वनिधी योजना": ["अर्ज", "स्थिती तपासा", "डाउनलोड फॉर्म"],
    "पीएम विश्वकर्मा योजना": ["अर्ज", "स्थिती तपासा", "डाउनलोड फॉर्म"],
    "अभय योजना": ["अर्ज", "स्थिती तपासा", "डाउनलोड फॉर्म"],
    "NULM अंतर्गत बचत गट कर्ज योजना": ["अर्ज", "स्थिती तपासा", "डाउनलोड फॉर्म"]
}

SCHEME_PROBLEMS = {
    "घरकुल आवास योजना": [
        "लाभार्थी नाव अंतिम यादीत नाही",
        "घरकुल मंजुरी मिळाली नाही",
        "कागदपत्रे तपासणी प्रलंबित",
        "हप्त्याचे पैसे मिळत नाहीत",
        "घर बांधकामास परवानगी मिळत नाही",
        "टप्प्याचे (प्रथम/द्वितीय/तृतीय) पैसे थांबले आहेत",
        "सर्व्हे/तपासणी अधिकारी वेळेवर भेट देत नाहीत",
        "चुकीची माहिती नोंदवली गेली",
        "घरकुल मंजुरी असूनही प्रत्यक्ष काम सुरू नाही"
    ],
    "रमाई आवास योजना": [
        "अर्ज मंजूर होत नाही",
        "जमिनीचे मोजमाप/सर्व्हे प्रलंबित",
        "घर बांधकामाचा निधी थांबलेला",
        "कागदपत्रे अपूर्ण दाखवत आहेत",
        "मंजूर पण बांधकाम काम सुरू नाही",
        "BPL/SECC यादीमध्ये नाव दिसत नाही",
        "अधिकाऱ्यांकडून योग्य मार्गदर्शन नाही"
    ],
    "पीएम स्वनिधी योजना": [
        "कर्ज मंजुरी मिळत नाही",
        "अर्जात चुकीची माहिती दाखवली गेली",
        "सबसिडी रक्कम मिळत नाही",
        "बँकेकडून अर्ज स्वीकारला जात नाही",
        "व्हेंडर आयडी व्हेरीफाय होत नाही",
        "EMI संपर्क न देता डेबिट झाली",
        "पोर्टलवर अर्ज अडकलेला (pending for verification)",
        "दस्तऐवज अपुर्ण / mismatch"
    ],
    "पीएम विश्वकर्मा योजना": [
        "नोंदणी होत नाही / OTP येत नाही",
        "कागदपत्रे व्हेरीफाय होत नाहीत",
        "प्रशिक्षण (Training) साठी बोलावत नाहीत",
        "टूलकिट मिळाले नाही",
        "आर्थिक मदत (loan) मंजूर होत नाही",
        "पोर्टलवर चुकीचा व्यवसाय टॅग झाला",
        "अर्जावर \"rejected\" कारण न देता दाखवला आहे"
    ],
    "अभय योजना": [
        "थकबाकी माफी दाखवत नाही",
        "अर्ज सबमिट केल्यानंतर अपडेट नाही",
        "चुकीची दंड आकारणी",
        "सवलत/माफी लागू होत नाही",
        "बिलवर चुकीची माहिती",
        "पोर्टलवर पेमेंट होत नाही",
        "कार्यालयात अर्ज स्वीकारत नाहीत"
    ],
    "NULM अंतर्गत बचत गट कर्ज योजना": [
        "SHG कर्ज मंजूर होत नाही",
        "महिला बचत गटाची यादी अपडेट होत नाही",
        "बँक अर्ज स्वीकारत नाही",
        "कागदपत्र mismatch दाखवत आहेत",
        "गट सभासदांची माहिती चुकीची नोंद",
        "व्याजदर / EMI चुकीचे वटवले",
        "गटाला revolving fund मिळत नाही",
        "बँक प्रगती अहवाल अपडेट करत नाही"
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

def gen_application_id():
    date_str = datetime.utcnow().strftime("%Y%m%d")
    rnd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"APP-{date_str}-{rnd}"

def insert_scheme_application(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    INSERT INTO scheme_applications (application_id, scheme_name, scheme_problem, prabhag, address, contact, email, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['application_id'],
        data['scheme_name'],
        data['scheme_problem'],
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

@app.route('/schemes')
def schemes():
    schemes_list = [
        {"key":"घरकुल आवास योजना", "label":"🏠 घरकुल आवास योजना"},
        {"key":"रमाई आवास योजना", "label":"🏠 रमाई आवास योजना"},
        {"key":"पीएम स्वनिधी योजना", "label":"💼 पीएम स्वनिधी योजना"},
        {"key":"पीएम विश्वकर्मा योजना", "label":"👷 पीएम विश्वकर्मा योजना"},
        {"key":"अभय योजना", "label":"🛡️ अभय योजना"},
        {"key":"NULM अंतर्गत बचत गट कर्ज योजना", "label":"💰 NULM अंतर्गत बचत गट कर्ज योजना"},
    ]
    return render_template('schemes.html', schemes=schemes_list)

@app.route('/choices')
def choices():
    cat = request.args.get('category')
    items = CHOICES.get(cat, [])
    return jsonify(items)

@app.route('/scheme_options')
def scheme_options():
    scheme = request.args.get('scheme')
    items = SCHEME_PROBLEMS.get(scheme, [])
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

@app.route('/scheme/<scheme_name>')
def scheme_form(scheme_name):
    return render_template('scheme_form.html', scheme_name=scheme_name)

@app.route('/submit_scheme', methods=['POST'])
def submit_scheme():
    data = request.json
    required = ['scheme_name', 'scheme_problem', 'prabhag', 'address', 'contact']
    for r in required:
        if not data.get(r):
            return jsonify({"status":"error", "message": f"Missing {r}"}), 400

    application_id = gen_application_id()
    data['application_id'] = application_id
    try:
        insert_scheme_application(data)
    except Exception as e:
        return jsonify({"status":"error", "message": str(e)}), 500

    return jsonify({"status":"ok", "application_id": application_id})

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

@app.route('/admin/resolve/<int:complaint_id>', methods=['POST'])
@admin_required
def admin_resolve(complaint_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE complaints SET resolved = 1 WHERE id = ?", (complaint_id,))
    conn.commit()
    conn.close()
    flash("Complaint marked as resolved.", "info")
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

    # Create CSV in-memory with UTF-8 BOM for proper encoding
    output = io.StringIO()
    # Write BOM for Excel to recognize UTF-8 properly
    output.write('\ufeff')
    writer = csv.writer(output)
    header = ['id','ticket_id','main_category','sub_category','prabhag','address','contact','email','created_at','resolved']
    writer.writerow(header)
    for r in rows:
        resolved_status = 'Yes' if r['resolved'] else 'No'
        writer.writerow([r['id'], r['ticket_id'], r['main_category'], r['sub_category'],
                         r['prabhag'], r['address'], r['contact'], r['email'], r['created_at'], resolved_status])
    output.seek(0)

    # send as attachment
    filename = f"complaints_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

# ---------- run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host='0.0.0.0', debug=True, port=port)
