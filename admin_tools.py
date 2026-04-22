import csv
import qrcode
import os
from werkzeug.security import generate_password_hash
from app import app, db, Event, Guest

def setup_event_and_qrs(name, code, password, csv_file):
    with app.app_context():
        # 1. Sajili Harusi
        event = Event.query.filter_by(event_code=code).first()
        if not event:
            event = Event(name=name, event_code=code, password_hash=generate_password_hash(password))
            db.session.add(event)
            db.session.commit()
            print(f"✅ Harusi '{name}' imesajiliwa!")

        # 2. Folder la QR
        path = f"static/qrs/{code}"
        os.makedirs(path, exist_ok=True)

        # 3. Pakia Wageni kutoka CSV na Generate QR
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Hakikisha mgeni hayupo tayari
                existing = Guest.query.filter_by(event_id=event.id, qr_code=row['code']).first()
                if not existing:
                    g = Guest(
                        event_id=event.id, 
                        name=row['name'], 
                        qr_code=row['code'], 
                        allowed=int(row['allowed'])
                    )
                    db.session.add(g)
                    
                    # TENGENEZA QR IMAGE
                    qr = qrcode.make(row['code'])
                    qr.save(f"{path}/{row['code']}.png")
                    print(f"   - QR ya {row['name']} imetengenezwa.")
        
        db.session.commit()
        print(f"\n🚀 Kila kitu kipo tayari kwa Harusi ya {name}!")

if __name__ == "__main__":
    # Badilisha hapa kulingana na mahitaji yako
    setup_event_and_qrs(
        name="Harusi ya Brian na Neema", 
        code="BRN2026", 
        password="Password123", 
        csv_file="guests_with_ids.csv"
    )