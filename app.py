import os
import csv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Pakia environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-brims-key')

# DATABASE CONNECTION
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    event_code = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    guests = db.relationship('Guest', backref='event', lazy=True, cascade="all, delete-orphan")

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    qr_code = db.Column(db.String(50), nullable=False)
    allowed = db.Column(db.Integer, default=1)
    used = db.Column(db.Integer, default=0)
    __table_args__ = (db.UniqueConstraint('event_id', 'qr_code', name='unique_guest_per_event'),)

# --- ONE-TIME DATABASE RESET & LOAD ---
with app.app_context(): 
    db.create_all()
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        event_code_input = request.form.get('event_code').strip().upper()
        password_input = request.form.get('password')
        
        target_event = Event.query.filter_by(event_code=event_code_input).first()
        
        if target_event and check_password_hash(target_event.password_hash, password_input):
            session['event_id'] = target_event.id
            session['event_name'] = target_event.name
            session['event_code'] = target_event.event_code
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
    if 'event_id' not in session:
        return redirect(url_for('login'))
    return render_template('scanner.html', event_name=session['event_name'])

@app.route('/scan', methods=['POST'])
def scan():
    if 'event_id' not in session:
        return jsonify({'status': 'error', 'message': 'Hujalogin!'}), 401
    
    data = request.get_json()
    code = data.get('code')
    
    guest = Guest.query.filter_by(event_id=session['event_id'], qr_code=code).first()
    
    if not guest:
        return jsonify({'status': 'invalid'})
        
    if guest.used < guest.allowed:
        guest.used += 1
        db.session.commit()
        return jsonify({'status': 'success', 'name': guest.name, 'used': guest.used, 'allowed': guest.allowed})
    else:
        return jsonify({'status': 'full', 'name': guest.name, 'used': guest.used, 'allowed': guest.allowed})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
