from extensions import db  # Pastikan import dari extensions

# 1. MODEL ADMIN
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nama = db.Column(db.String(100))

    def to_dict(self):
        return {"id": self.id, "email": self.email, "nama": self.nama}

# 2. MODEL PENGGUNA
class Pengguna(db.Model):
    __tablename__ = 'pengguna'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    umur = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    tinggi = db.Column(db.Integer)
    berat = db.Column(db.Integer)
    poin = db.Column(db.Integer, default=0)
    
    # --- TAMBAHKAN BARIS INI AGAR TIDAK ERROR ---
    foto = db.Column(db.String(255)) 
    # --------------------------------------------

    # Relasi (Biarkan seperti semula)
    riwayat_makan = db.relationship('RiwayatMakan', backref='pengguna', lazy=True, cascade="all, delete-orphan")
    riwayat_aktivitas = db.relationship('RiwayatAktivitas', backref='pengguna', lazy=True, cascade="all, delete-orphan")
    riwayat_lari = db.relationship('RiwayatLari', backref='pengguna', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "nama": self.nama, "email": self.email,
            "umur": self.umur, "gender": self.gender,
            "tinggi": self.tinggi, "berat": self.berat, "poin": self.poin,
            "foto": self.foto # Boleh ditambahkan ke sini juga
        }

# 3. MODEL RIWAYAT MAKAN (INI YANG HILANG TADI)
class RiwayatMakan(db.Model):
    __tablename__ = 'riwayat_makan'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('pengguna.id'), nullable=False)
    nama_makanan = db.Column(db.String(100), nullable=False)
    kalori = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    lemak = db.Column(db.Float, nullable=False)
    karbo = db.Column(db.Float, nullable=False)
    waktu_makan = db.Column(db.String(20), nullable=False) 
    tanggal = db.Column(db.String(20), nullable=False) 

    def to_dict(self):
        return {
            "id": self.id, "nama_makanan": self.nama_makanan,
            "kalori": self.kalori, "protein": self.protein,
            "lemak": self.lemak, "karbo": self.karbo,
            "waktu_makan": self.waktu_makan, "tanggal": self.tanggal
        }

# 4. MODEL RIWAYAT AKTIVITAS
class RiwayatAktivitas(db.Model):
    __tablename__ = 'riwayat_aktivitas'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('pengguna.id'), nullable=False)
    aktivitas = db.Column(db.String(100))
    waktu = db.Column(db.String(50))
    kalori = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id,
            "aktivitas": self.aktivitas, "waktu": self.waktu, "kalori": self.kalori
        }

# 5. MODEL KONTEN
class Konten(db.Model):
    __tablename__ = 'konten_edukasi'
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(200), nullable=False)
    kategori = db.Column(db.String(100), nullable=False)
    publikasi = db.Column(db.String(20), nullable=False)
    tautan = db.Column(db.String(255), nullable=False)
    foto = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id, "judul": self.judul, "kategori": self.kategori,
            "publikasi": self.publikasi, "tautan": self.tautan, "foto": self.foto
        }

# 6. MODEL LAPORAN
class Laporan(db.Model):
    # Pastikan nama ini SAMA PERSIS dengan nama tabel di PhpMyAdmin
    # Kalau di database namanya 'laporan', ganti jadi 'laporan'
    __tablename__ = 'laporan' 

    id = db.Column(db.Integer, primary_key=True)
    pengguna = db.Column(db.String(100))
    tanggal = db.Column(db.String(20))
    deskripsi = db.Column(db.Text)
    status = db.Column(db.String(50))
    image = db.Column(db.String(255))

    # --- TAMBAHAN BARU ---
    email = db.Column(db.String(100)) 
    jenis = db.Column(db.String(50))  

    def to_dict(self):
        return {
            "id": self.id, 
            "pengguna": self.pengguna, 
            
            # JANGAN LUPA MASUKKAN INI KE JSON:
            "email": self.email,  
            "jenis": self.jenis,
            
            "tanggal": self.tanggal, 
            "deskripsi": self.deskripsi, 
            "status": self.status, 
            "image": self.image
        }
    
class Makanan(db.Model):
    __tablename__ = 'foods'  # <--- GANTI INI (Sesuaikan dengan nama tabel di phpMyAdmin tadi)
    
    id = db.Column(db.Integer, primary_key=True)
    # Sesuaikan nama kolom dengan yang ada di database kamu
    name = db.Column(db.String(255), nullable=False)  
    calories = db.Column(db.Float, nullable=False)
    proteins = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    carbohydrate = db.Column(db.Float, nullable=False)
    image = db.Column(db.Text) 

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name,
            "calories": self.calories, 
            "proteins": self.proteins,
            "fat": self.fat, 
            "carbohydrate": self.carbohydrate,
            "image": self.image
        }

# ... (kode model lain di atas tetap sama)

# 7. MODEL KHUSUS LARI (Baru)
class RiwayatLari(db.Model):
    __tablename__ = 'riwayat_lari'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('pengguna.id'), nullable=False)
    
    jarak = db.Column(db.Float, nullable=False)    # Contoh: 5.2 (km)
    waktu = db.Column(db.String(50), nullable=False) # Contoh: "00:30:00"
    kalori = db.Column(db.Integer, nullable=False) # Contoh: 200
    tanggal = db.Column(db.String(20), nullable=False) # Contoh: "2025-12-20"
    
    # Opsi: Kalau mau simpan rute (titik koordinat banyak), pakai Text
    rute = db.Column(db.Text, nullable=True) 

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "jarak": self.jarak,
            "waktu": self.waktu,
            "kalori": self.kalori,
            "tanggal": self.tanggal,
            "rute": self.rute
        }