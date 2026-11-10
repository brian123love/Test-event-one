import os
import csv
import qrcode
from app import app, db, Event, Guest
from werkzeug.security import generate_password_hash

def register_new_wedding(name, code, password, csv_file):
    with app.app_context():
        # 1. Pata au Sajili Harusi
        event = Event.query.filter_by(event_code=code.upper()).first()
        if not event:
            event = Event(
                name=name, 
                event_code=code.upper(), 
                password_hash=generate_password_hash(password)
            )
            db.session.add(event)
            db.session.commit()
            print(f"\n✅ Harusi mpya '{name}' imesajiliwa!")
        else:
            print(f"\nℹ️ Harusi '{code}' ipo tayari. Tunaangalia wageni wapya...")

        # 2. Folder la QR codes
        qr_folder = f"static/qrs/{code.upper()}"
        if not os.path.exists(qr_folder):
            os.makedirs(qr_folder)

        # 3. Kupakia wageni na kutengeneza QR codes (Wapya tu)
        if os.path.exists(csv_file):
            with open(csv_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                added_to_db = 0
                added_qr_images = 0
                
                for row in reader:
                    guest_code = row['code']
                    # A. Angalia kama mgeni yupo kwenye Database
                    existing_guest = Guest.query.filter_by(event_id=event.id, qr_code=guest_code).first()
                    
                    if not existing_guest:
                        new_guest = Guest(
                            event_id=event.id,
                            name=row['name'],
                            qr_code=guest_code,
                            allowed=int(row['allowed'])
                        )
                        db.session.add(new_guest)
                        added_to_db += 1
                    
                    # B. Angalia kama picha ya QR tayari ipo kwenye folder
                    img_path = f"{qr_folder}/{guest_code}.png"
                    if not os.path.exists(img_path):
                        qr_img = qrcode.make(guest_code)
                        qr_img.save(img_path)
                        added_qr_images += 1
                
                db.session.commit()
                print(f"📊 MATOKEO:")
                print(f"   - Wageni wapya walioongezwa database: {added_to_db}")
                print(f"   - Picha za QR mpya zilizotengenezwa: {added_qr_images}")
                print(f"📁 Picha zipo hapa: {qr_folder}")
        else:
            print(f"⚠️ Kosa: Faili la '{csv_file}' halipo!")

if __name__ == "__main__":
    print("\n" + "="*30)
    print("   BRIM'S EVENT MANAGER PRO")
    print("="*30)
    print("1. Ongeza/Update Harusi na Wageni")
    print("2. Angalia Harusi Zilizopo")
    
    choice = input("\nChagua namba: ")

    if choice == "1":
        code = input("Ingiza Event Code (mf: SAM2026): ").upper()
        # Kama event ipo, jina na password havitabadilika, lakini lazima uweke kitu
        name = input("Jina la Harusi: ")
        password = input("Password ya MC: ")
        csv_file = input("Jina la faili la CSV (mf: sam.csv): ")
        
        register_new_wedding(name, code, password, csv_file)
        
    elif choice == "2":
        with app.app_context():
            events = Event.query.all()
            print("\n--- LIST YA HARUSI ZILIZOPO ---")
            for e in events:
                print(f"🔹 [{e.event_code}] - {e.name}")
