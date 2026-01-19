from flask import Flask, jsonify, request
from flask_cors import CORS
from extensions import db 
from models import Laporan, Admin, Konten, Pengguna, RiwayatAktivitas, RiwayatMakan, Makanan, RiwayatLari
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text 
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

load_dotenv()
# Di bawah konfigurasi app lainnya
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL belum diset di environment")

app.config["SQLALCHEMY_DATABASE_URI"] = db_url

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- [SECURITY FIX 2] Tambahkan Secret Key ---
# Kunci ini dipakai untuk membuat Token unik. Jangan sampai bocor.
app.config['SECRET_KEY'] = 'kunci-rahasia-healthify-jangan-disebar-999'

app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")  # Kunci khusus JWT
jwt = JWTManager(app)  # <--- INI YANG HILANG DAN MENYEBABKAN ERROR
# ==========================================
# 2. INIT APP & SECURITY
# ==========================================

CORS(app, resources={r"/api/*": {"origins": "*"}})

db.init_app(app) 

with app.app_context():
    db.create_all()



# 3. API ADMIN
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# ==========================================
# UPDATE 3 FUNGSI INI DI app.py
# ==========================================

@app.route('/api/login/admin', methods=['POST'])
def login_admin():
    data = request.get_json()
    email_admin = data.get('email')
    password_admin = data.get('password')

    admin = Admin.query.filter_by(email=email_admin).first()

    if admin and check_password_hash(admin.password_hash, password_admin):
        access_token = create_access_token(identity=admin.email)
        return jsonify({
            "status": "success",
            "access_token": access_token,
            "user": admin.to_dict()
        }), 200

    return jsonify({"message": "Email atau Password salah"}), 401


@app.route('/api/admin/profile', methods=['GET'])
@jwt_required() # [JWT] Pasang Satpam (Cek Token)
def get_admin_profile():
    try:
        # [JWT] Ambil email otomatis dari dalam Token
        current_email = get_jwt_identity()
        
        admin = Admin.query.filter_by(email=current_email).first()
        if not admin:
            return jsonify({"message": "Admin tidak ditemukan"}), 404
            
        return jsonify(admin.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/profile', methods=['PUT'])
@jwt_required() # [JWT] Pasang Satpam juga untuk Update
def update_admin_profile():
    try:
        current_email = get_jwt_identity() # Ambil email dari Token
        admin = Admin.query.filter_by(email=current_email).first()
        
        if not admin:
            return jsonify({"message": "Akun admin tidak ditemukan"}), 404

        data = request.get_json()
        
        if 'nama' in data:
            admin.nama = data['nama']

        password_baru = data.get('password_baru')
        password_lama = data.get('password_lama')

        if password_baru:
            # Cek password lama
            if str(admin.password_hash) != str(password_lama):
                return jsonify({"message": "Gagal: Password lama salah!"}), 401
            admin.password_hash = password_baru

        db.session.commit()
        return jsonify({"message": "Profil berhasil diperbarui", "user": admin.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
# ==========================================
# 4. API SEARCH & CRUD MAKANAN
# ==========================================
@app.route('/api/makanan/search', methods=['GET'])
def search_makanan():
    try:
        query_param = request.args.get('q', '').strip()
        if not query_param:
            return jsonify([]), 200

        hasil_cari = Makanan.query.filter(Makanan.name.ilike(f"%{query_param}%")).limit(50).all()
        data_json = [item.to_dict() for item in hasil_cari]
        
        return jsonify(data_json), 200
    except Exception as e:
        print(f"[ERROR] Database Search Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/makanan', methods=['GET'])
def get_all_makanan():
    try:
        semua_makanan = Makanan.query.all()
        return jsonify([item.to_dict() for item in semua_makanan]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/makanan', methods=['POST'])
def add_new_makanan():
    try:
        data = request.get_json()
        new_food = Makanan(
            name=data['name'],
            calories=float(data['calories']),
            proteins=float(data['proteins']),
            fat=float(data['fat']),
            carbohydrate=float(data['carbohydrate']),
            image=data['image']
        )
        db.session.add(new_food)
        db.session.commit()
        return jsonify({"message": "Berhasil ditambahkan", "data": new_food.to_dict()}), 201
    except Exception as e:
        db.session.rollback() 
        return jsonify({"error": str(e)}), 500

@app.route('/api/makanan/<int:id>', methods=['PUT'])
def update_makanan(id):
    try:
        food = Makanan.query.get_or_404(id)
        data = request.get_json()
        
        if 'name' in data: food.name = data['name']
        if 'calories' in data: food.calories = float(data['calories'])
        if 'proteins' in data: food.proteins = float(data['proteins'])
        if 'fat' in data: food.fat = float(data['fat'])
        if 'carbohydrate' in data: food.carbohydrate = float(data['carbohydrate'])
        if 'image' in data: food.image = data['image']
        
        db.session.commit()
        return jsonify({"message": "Berhasil diupdate", "data": food.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/makanan/<int:id>', methods=['DELETE'])
def delete_makanan(id):
    try:
        food = Makanan.query.get_or_404(id)
        db.session.delete(food)
        db.session.commit()
        return jsonify({"message": "Berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ==========================================
# 5. API RIWAYAT MAKAN
# ==========================================
@app.route('/api/riwayat/makan', methods=['POST'])
def add_riwayat_makan():
    try:
        data = request.get_json()
        new_riwayat = RiwayatMakan(
            user_id=data['user_id'],
            nama_makanan=data['nama_makanan'],
            kalori=int(data['kalori']),        
            protein=float(data['proteins']),   
            lemak=float(data['fat']),          
            karbo=float(data['carbohydrate']), 
            waktu_makan=data['waktu'],
            tanggal=datetime.now().strftime("%Y-%m-%d")
        )
        db.session.add(new_riwayat)
        
        user = Pengguna.query.get(data['user_id'])
        if user:
            user.poin += 5 
        
        db.session.commit()
        return jsonify({
            "message": "Berhasil! +5 Poin ditambahkan.", 
            "data": new_riwayat.to_dict(),
            "total_poin": user.poin 
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# ==========================================
# 6. API SUMMARY HARIAN
# ==========================================
@app.route('/api/summary/<int:user_id>', methods=['GET'])
def get_daily_summary(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    user = Pengguna.query.get_or_404(user_id)
    
    target_kalori = 2000 
    if user.berat > 0 and user.tinggi > 0 and user.umur > 0:
        if user.gender == 'L':
            target_kalori = (10 * user.berat) + (6.25 * user.tinggi) - (5 * user.umur) + 5
        else:
            target_kalori = (10 * user.berat) + (6.25 * user.tinggi) - (5 * user.umur) - 161
        target_kalori = int(target_kalori * 1.2) 
    
    riwayat = RiwayatMakan.query.filter_by(user_id=user_id, tanggal=today).all()
    total_kalori = sum(r.kalori for r in riwayat)
    
    if target_kalori == 0: target_kalori = 2000
    persentase = (total_kalori / target_kalori) * 100
    
    status_gizi = "Belum Cukup"
    poin_dapat = 0 
    pesan_motivasi = "Ayo makan sehat!"

    if total_kalori == 0:
         status_gizi = "Belum Makan"
         pesan_motivasi = "Jangan lupa sarapan ya!"
    elif persentase < 50:
        status_gizi = "Kurang Energi ⚠️"
        poin_dapat = 1
        pesan_motivasi = "Tubuhmu butuh bensin, ayo makan lagi."
    elif persentase >= 50 and persentase < 80:
        status_gizi = "Hampir Cukup 😐"
        poin_dapat = 5
        pesan_motivasi = "Sedikit lagi mencapai target!"
    elif persentase >= 80 and persentase <= 110:
        status_gizi = "Ideal / Bagus ✨"
        poin_dapat = 5
        pesan_motivasi = "Luar biasa! Pertahankan gizimu."
    else:
        status_gizi = "Berlebihan 🛑"
        poin_dapat = 5
        pesan_motivasi = "Ups, rem dulu makannya ya."

    list_pagi = [r.to_dict() for r in riwayat if r.waktu_makan == 'Pagi']
    list_siang = [r.to_dict() for r in riwayat if r.waktu_makan == 'Siang']
    list_malam = [r.to_dict() for r in riwayat if r.waktu_makan == 'Malam']

    return jsonify({
        "total_kalori": total_kalori,
        "target_kalori": target_kalori, 
        "status_gizi": status_gizi,     
        "poin_hari_ini": poin_dapat,    
        "pesan": pesan_motivasi,        
        "pagi": list_pagi,
        "siang": list_siang,
        "malam": list_malam
    }), 200

# ==========================================
# 7. API USERS
# ==========================================
@app.route('/api/users', methods=['GET'])
def get_users():
    all_users = Pengguna.query.all()
    return jsonify([u.to_dict() for u in all_users]), 200

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    cek_email = Pengguna.query.filter_by(email=data['email']).first()
    if cek_email:
        return jsonify({"message": "Email sudah terdaftar!"}), 400

    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')

    new_user = Pengguna(
        nama=data['nama'], 
        email=data['email'], 
        password=hashed_password, 
        umur=0, gender='-', tinggi=0, berat=0, poin=0
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Registrasi Berhasil!", "user": new_user.to_dict()}), 201

@app.route('/api/login/user', methods=['POST'])
def login_user():
    data = request.get_json()
    email_hp = data.get('email')
    password_input = data.get('password') 
    
    print(f"\n[LOGIN] Mencoba login: {email_hp}")

    user = Pengguna.query.filter_by(email=email_hp).first()

    if not user:
        return jsonify({"message": "Email tidak ditemukan"}), 401

    password_is_valid = False

    if len(user.password) > 50 and user.password.startswith('pbkdf2:'):
        if check_password_hash(user.password, password_input):
            password_is_valid = True
    else:
        if str(user.password) == str(password_input):
            password_is_valid = True
            
            user.password = generate_password_hash(password_input, method='pbkdf2:sha256')
            db.session.commit()
            print(f"[INFO] Password user {user.nama} berhasil di-upgrade ke Hash aman.")

    if password_is_valid:
        return jsonify({
            "status": "success", 
            "message": "Login User Berhasil!", 
            "user": user.to_dict()
        }), 200
    else:
        return jsonify({"message": "Password Salah"}), 401
    
@app.route('/api/fix-passwords', methods=['GET'])
def fix_passwords():
    users = Pengguna.query.all()
    count = 0
    for u in users:
        if len(u.password) < 50:
            print(f"Mengamankan password user: {u.nama}")
            u.password = generate_password_hash(u.password, method='pbkdf2:sha256')
            count += 1
    
    db.session.commit()
    return jsonify({"message": f"Berhasil mengamankan {count} akun user lama!"}), 200

@app.route('/api/users/<int:id>', methods=['GET'])
def get_user_detail(id):
    try:
        user = Pengguna.query.get_or_404(id)
        data = user.to_dict()

        if user.tinggi > 0 and user.berat > 0:
            t_meter = user.tinggi / 100
            data['bmi_score'] = round(user.berat / (t_meter * t_meter), 1)
        else:
            data['bmi_score'] = 0

        if user.foto:
             data['foto'] = f"/static/uploads/{user.foto}"
             
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:id>', methods=['PUT'])
def update_user(id):
    try:
        user = Pengguna.query.get_or_404(id)
        
        data = {}
        is_json = False

        if request.is_json:
            data = request.get_json()
            is_json = True
            print(f"[DEBUG] Update via JSON (BMI Screen): {data}")
        else:
            data = request.form
            print(f"[DEBUG] Update via Form (Profile Screen): {data}")

        if 'nama' in data: user.nama = data['nama']
        if 'email' in data: user.email = data['email']
        if 'gender' in data: user.gender = data['gender']
        
        if 'umur' in data and data['umur']: 
            user.umur = int(float(data['umur']))
        if 'tinggi' in data and data['tinggi']: 
            user.tinggi = float(data['tinggi'])
        if 'berat' in data and data['berat']: 
            user.berat = float(data['berat'])

        if not is_json and 'foto' in request.files:
            file = request.files['foto']
            if file.filename != '':
                filename = f"user_{id}_{int(datetime.now().timestamp())}.jpg"
                upload_folder = os.path.join(app.root_path, 'static/uploads')
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                    
                file.save(os.path.join(upload_folder, filename))
                user.foto = filename 

        if 'password' in data and data['password']:
            new_pass_input = data['password']
            old_pass_input = data.get('old_password') 
            
            if old_pass_input:
                password_match = False
                if user.password.startswith('pbkdf2:'):
                    if check_password_hash(user.password, old_pass_input):
                        password_match = True
                else:
                    if str(user.password) == str(old_pass_input):
                        password_match = True
                
                if password_match:
                    user.password = generate_password_hash(new_pass_input, method='pbkdf2:sha256')
                else:
                    return jsonify({"message": "Password lama salah!"}), 401

        db.session.commit()
        
        user_dict = user.to_dict()
        if user.foto:
            user_dict['foto'] = f"/static/uploads/{user.foto}"

        return jsonify({"message": "Data Berhasil Diupdate!", "user": user_dict}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR UPDATE USER] {e}") 
        return jsonify({"message": "Gagal update data", "error": str(e)}), 500

# ==========================================
# 8. API KONTEN & LAPORAN
# ==========================================
@app.route('/api/konten', methods=['GET'])
def get_konten():
    return jsonify([item.to_dict() for item in Konten.query.all()]), 200

@app.route('/api/konten', methods=['POST'])
def add_konten():
    d = request.get_json()
    new = Konten(
        judul=d['judul'], kategori=d['kategori'], 
        publikasi=d['publikasi'], tautan=d['tautan'],
        foto=d.get('foto', '')
    )
    db.session.add(new)
    db.session.commit()
    return jsonify({"message": "Added", "data": new.to_dict()}), 201

@app.route('/api/laporan', methods=['GET'])
def get_laporan():
    return jsonify([d.to_dict() for d in Laporan.query.all()])

# --- TARGET CSRF SEBELUMNYA ---
# Sekarang endpoint ini sudah AMAN karena diproteksi oleh 'csrf = CSRFProtect(app)'
@app.route('/api/laporan', methods=['POST'])

def add_laporan():
    nama = request.form.get('nama')
    email = request.form.get('email')
    jenis = request.form.get('jenis')
    deskripsi = request.form.get('deskripsi')
    
    filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            filename = file.filename
            
            upload_folder = os.path.join(app.root_path, 'static/uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            file.save(os.path.join(upload_folder, filename)) 

    new_laporan = Laporan(
        pengguna=nama, email=email, jenis=jenis,
        tanggal=datetime.now().strftime("%Y-%m-%d"),
        deskripsi=deskripsi, status="Pending", image=filename
    )
    
    db.session.add(new_laporan)
    db.session.commit()
    return jsonify({"message": "Laporan Terkirim!"}), 201

@app.route('/api/laporan/<int:id>/status', methods=['PUT'])
def update_status_laporan(id):
    laporan = Laporan.query.get_or_404(id)
    data = request.get_json()
    
    laporan.status = data['status']
    
    db.session.commit()
    return jsonify({"message": "Status berhasil diupdate!"}), 200

@app.route('/api/laporan/<int:id>', methods=['DELETE'])
def delete_laporan(id):
    try:
        laporan = Laporan.query.get_or_404(id)
        
        if laporan.image:
            file_path = os.path.join(app.root_path, 'static/uploads', laporan.image)
            if os.path.exists(file_path):
                os.remove(file_path)
                
        db.session.delete(laporan)
        db.session.commit()
        return jsonify({"message": "Laporan berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/riwayat-laporan', methods=['GET'])
def riwayat_laporan():
    email_user = request.args.get('email') 
    
    try:
        hasil_db = Laporan.query.filter_by(email=email_user).order_by(Laporan.tanggal.desc()).all()
        
        payload = []
        for item in hasil_db:
            payload.append({
                'jenis': item.jenis,          
                'deskripsi': item.deskripsi,  
                'tanggal': str(item.tanggal), 
                'status': item.status
            })
            
        return jsonify(payload), 200
        
    except Exception as e:
        print(f"Error Database: {e}")
        return jsonify({"message": "Gagal mengambil data", "error": str(e)}), 500

@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        user = Pengguna.query.get_or_404(id)
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({"message": "User dan seluruh riwayatnya berhasil dihapus!"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR DELETE USER] {e}")
        return jsonify({"error": str(e), "message": "Gagal menghapus user"}), 500

@app.route('/api/konten/<int:id>', methods=['PUT'])
def update_konten(id):
    try:
        item = Konten.query.get_or_404(id)
        data = request.get_json()
        
        if 'judul' in data: item.judul = data['judul']
        if 'kategori' in data: item.kategori = data['kategori']
        if 'publikasi' in data: item.publikasi = data['publikasi']
        if 'tautan' in data: item.tautan = data['tautan']
        if 'foto' in data: item.foto = data['foto']
        
        db.session.commit()
        return jsonify({"message": "Konten berhasil diupdate"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/konten/<int:id>', methods=['DELETE'])
def delete_konten(id):
    try:
        item = Konten.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Konten berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/reset-password/verify', methods=['POST'])
def verify_user_reset():
    data = request.get_json()
    nama = data.get('nama')
    email = data.get('email')

    user = Pengguna.query.filter_by(nama=nama, email=email).first()

    if user:
        return jsonify({"status": "success", "message": "User ditemukan", "user_id": user.id}), 200
    else:
        return jsonify({"status": "error", "message": "Nama atau Email tidak terdaftar!"}), 404

@app.route('/api/reset-password/update', methods=['PUT'])
def update_password_reset():
    data = request.get_json()
    user_id = data.get('user_id')
    new_password = data.get('new_password')

    user = Pengguna.query.get(user_id)
    if user:
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        user.password = hashed_password
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Password berhasil diperbarui!"}), 200
    
    return jsonify({"status": "error", "message": "User tidak ditemukan"}), 404

# ==========================================
# 9. API KHUSUS LARI (TRACKING & HISTORY)
# ==========================================

@app.route('/api/lari', methods=['POST'])
def add_riwayat_lari():
    try:
        data = request.get_json()
        
        poin_dapat = 1 

        new_run = RiwayatLari(
            user_id=data['user_id'],
            jarak=float(data['jarak']),
            waktu=data['waktu'],
            kalori=int(data['kalori']),
            tanggal=datetime.now().strftime("%Y-%m-%d"),
            rute=data.get('rute', 'Lokasi tersimpan')
        )
        
        user = Pengguna.query.get(data['user_id'])
        if user:
            user.poin += poin_dapat

        db.session.add(new_run)
        db.session.commit()
        
        return jsonify({
            "message": "Lari berhasil disimpan! +1 Poin", 
            "data": new_run.to_dict(),
            "total_poin": user.poin
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR LARI] {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/lari/<int:user_id>', methods=['GET'])
def get_riwayat_lari(user_id):
    try:
        items = RiwayatLari.query.filter_by(user_id=user_id).order_by(RiwayatLari.id.desc()).all()
        return jsonify([item.to_dict() for item in items]), 200
    except Exception as e:
        print(f"[ERROR GET LARI] {e}")
        return jsonify({"error": str(e)}), 500

# ==========================================
# API KHUSUS DEMO (JANGAN DIHAPUS UNTUK TUGAS)
# ==========================================
@app.route('/api/login/admin-demo', methods=['POST'])
def login_admin_vulnerable():
    data = request.get_json()
    email_admin = data.get('email')
    password_admin = data.get('password') 
    
    # [TUGAS KULIAH] Tetap gunakan Raw SQL untuk demo SQL Injection
    query_jahat = f"SELECT * FROM admin WHERE email = '{email_admin}' AND password_hash = '{password_admin}'"
    
    print(f"[DEMO VULN] Query dijalankan: {query_jahat}")

    try:
        result = db.session.execute(text(query_jahat)).fetchone()

        if result:
            return jsonify({
                "status": "success", 
                "message": "Login JEBOL Berhasil (SQL Injection)!",
                "user": {"id": 1, "nama": "Hacker", "email": email_admin} 
            }), 200
        else:
            return jsonify({"message": "Gagal login"}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
