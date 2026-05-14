import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables (for local testing, Render will use its own env vars)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-brims-key')

# DATABASE CONNECTION
# -----------------------------
# Get Render DATABASE_URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

# FIX 1: SQLAlchemy requires 'postgresql://' but Render provides 'postgres://'
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# PostgreSQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False) # Mfano: "Harusi ya Juma & Neema"
    event_code = db.Column(db.String(50), unique=True, nullable=False) # Mfano: "JUMA2026"
    password_hash = db.Column(db.String(256), nullable=False) # Password ya scanner
    guests = db.relationship('Guest', backref='event', lazy=True, cascade="all, delete-orphan")

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    qr_code = db.Column(db.String(50), nullable=False) # Mfano: SO-12
    allowed = db.Column(db.Integer, default=1)
    used = db.Column(db.Integer, default=0)
    
    # Hii inahakikisha qr_code ni unique ndani ya event moja tu
    __table_args__ = (db.UniqueConstraint('event_id', 'qr_code', name='unique_guest_per_event'),)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        event_code = request.form.get('event_code').strip().upper()
        password = request.form.get('password')
        
        event = Event.query.filter_by(event_code=event_code).first()
        
        # Ensures only MCs, DJs, or authorized scanners with passwords can access this
        if event and check_password_hash(event.password_hash, password):
            session['event_id'] = event.id
            session['event_name'] = event.name
            session['event_code'] = event.event_code
            return redirect(url_for('scanner'))
        else:
            return render_template('login.html', error="Event Code au Password sio sahihi.")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def scanner():
    # Hakikisha scanner amelogin
    if 'event_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('scanner.html', event_name=session['event_name'])

@app.route('/scan', methods=['POST'])
def scan():
    if 'event_id' not in session:
        return jsonify({'status': 'error', 'message': 'Hujalogin!'}), 401
        
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'status': 'invalid', 'message': 'No code provided'}), 400

    current_event_id = session['event_id']
    
    # Tafuta mgeni KWA KUTUMIA EVENT ID YA HARUSI HUSIKA TU
    guest = Guest.query.filter_by(event_id=current_event_id, qr_code=code).first()
    
    if not guest:
        return jsonify({'status': 'invalid', 'name': None, 'used': 0, 'allowed': 0})
        
    # FIX 2: Corrected attributes from used_entries/allowed_entries to used/allowed
    if guest.used < guest.allowed:
        guest.used += 1
        db.session.commit()
        return jsonify({
            'status': 'success',
            'name': guest.name,
            'used': guest.used,
            'allowed': guest.allowed
        })
    else:
        return jsonify({
            'status': 'full',
            'name': guest.name,
            'used': guest.used,
            'allowed': guest.allowed
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
