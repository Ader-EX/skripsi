# FastAPI Project || PENJADWALAN OTOMATIS

## Frontend Repository

Frontend: [https://github.com/Ader-EX/skripsi-fe](https://github.com/Ader-EX/skripsi-fe)

## Deskripsi Proyek

### Deksripsi Singkat

Penjadwalan memiliki peran penting di lingkungan perguruan tinggi dalam memastikan proses akademik berjalan dengan lancar. Meskipun terlihat sederhana, proses penjadwalan ini bersifat kompleks karena melibatkan banyak faktor seperti ketersediaan ruangan, waktu, mata kuliah yang dibuka, serta preferensi mengajar dosen. Di Fakultas Ilmu Komputer Universitas Pembangunan Nasional "Veteran" Jakarta, proses penjadwalan masih dilakukan secara manual, sehingga seringkali tidak mampu mengakomodasi preferensi dosen secara optimal dan membutuhkan waktu yang lama.

Penelitian ini bertujuan untuk mengembangkan _Smart Scheduling System_ berbasis web dengan yang menggunakan Next.js sebagai kerangka kerja _frontend_ dan FastAPI di sisi _backend_, dengan pendekatan Algoritma Genetika dan _Simulated Annealing_ untuk membuat jadwal yang optimal dan diterima oleh seluruh pengguna. Pengujian dilakukan dengan _User Acceptance Testing_ terhadap tiga jenis pengguna: mahasiswa, dosen, dan admin. Hasil pengujian menunjukkan bahwa sistem memperoleh penilaian rata-rata di atas 90%, yang menandakan bahwa sistem telah diterima secara baik dan memenuhi kebutuhan pengguna. Penelitian ini diharapkan mampu menghasilkan jadwal perkuliahan yang efisien dan dapat meningkatkan kepuasan dosen dan efisiensi kerja staf akademik dalam membuat jadwal perkuliahan.

## Teknologi yang Digunakan

### Backend

- FastAPI - Framework Python untuk membangun API dengan performa tinggi
- SQLAlchemy - ORM (Object Relational Mapper) untuk database
- MySQL - Database relasional
- Pydantic - Validasi data dan pengaturan
- JWT - Autentikasi berbasis token
- DBeaver - Akses DB secara mudah

### Frontend

- Next.js - Framework React untuk aplikasi web
- React - Library JavaScript untuk membangun antarmuka pengguna
- Tailwind CSS - Framework CSS untuk styling
- ShadCN - Component builder sebagai dasar antarmuka yang ada

### Algoritma

- Algoritma Genetika - Untuk optimasi penjadwalan
- Simulated Annealing - Untuk penyempurnaan solusi dari algoritma genetika

## Fitur Utama

1. **Autentikasi Pengguna**

   - Login dan register untuk tiga jenis pengguna (Admin, Dosen, Mahasiswa)
   - JWT-based authentication
   - Role-based access control

2. **Manajemen Data**

   - CRUD untuk mata kuliah
   - CRUD untuk dosen
   - CRUD untuk ruangan
   - CRUD untuk preferensi dosen

3. **Penjadwalan Otomatis**

   - Algoritma Genetika untuk menghasilkan jadwal awal
   - Simulated Annealing untuk optimasi jadwal
   - Mempertimbangkan berbagai batasan (constraints)

4. **Dashboard**

   - Dashboard Admin untuk manajemen sistem
   - Dashboard Dosen untuk melihat jadwal dan mengatur preferensi
   - Dashboard Mahasiswa untuk melihat jadwal

5. **Visualisasi Jadwal**
   - Tampilan jadwal dalam format mingguan
   - Filter jadwal berdasarkan program studi, semester, dll.
   - Export jadwal ke PDF dan Excel

### Setup

1. Clone the repository:

   ```
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   ```

3. Activate the virtual environment:

   - Windows:
     ```
     venv\Scripts\activate || venv\Scripts\activate.bat
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

5. Change the directory to:

   ```
   cd backend
   ```

6. Run the application:
   ```
   uvicorn main:app --reload
   ```

### Frontend (Next.js)

1. Navigate to the frontend directory:

   ```
   cd frontend
   ```

2. Install dependencies:

   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```

The application will be available at:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000) and
- [http://localhost:8000/docs](http://localhost:8000/docs) to access the backend documentation

## Deployment

Proyek ini menggunakan dua platform deployment:

### Frontend (Next.js) dengan Vercel

1. Buat akun di [Vercel](https://vercel.com)
2. Hubungkan repository GitHub Anda
3. Pilih repository frontend Anda
4. Konfigurasi variabel lingkungan yang diperlukan:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   ```
5. Deploy

### Backend (FastAPI) dengan Google Cloud Platform (GCP)

1. Buat project baru di [Google Cloud Console](https://console.cloud.google.com/)

2. Aktifkan Cloud Build API, Container Registry API, dan Cloud Run API

3. Instal Google Cloud SDK di komputer lokal Anda

4. Login ke Google Cloud:

   ```
   gcloud auth login
   ```

5. Pilih project:

   ```
   gcloud config set project skripsi-be-452603
   ```

6. Build dan push container image:

   ```
   gcloud builds submit --tag asia-southeast1-docker.pkg.dev/skripsi-be-452603/skripsi-be/skripsi-beimg:skripsi-betag
   ```

7. Deploy ke Cloud Run:
   - Buka [Cloud Run Console](https://console.cloud.google.com/run)
   - Klik "Deploy Container"
   - Pilih container yang baru saja di-build
   - Konfigurasi deployment (CPU, memory, variabel lingkungan)
   - Deploy

### Cara Update/Revisi Backend

Untuk memperbarui backend setelah melakukan perubahan:

1. Commit perubahan Anda ke repository
2. Build dan push image baru:
   ```
   gcloud builds submit --tag asia-southeast1-docker.pkg.dev/skripsi-be-452603/skripsi-be/skripsi-beimg:skripsi-betag
   ```
3. Buka Cloud Run di Google Cloud Console
4. Pilih service Anda
5. Klik "Add new revision"
6. Pilih image yang baru diperbarui
7. Deploy revision baru

## Constraints dalam Algoritma Penjadwalan

### Hard Constraints (Harus dipenuhi)

- Tidak boleh ada jadwal yang tumpang tindih untuk dosen yang sama
- Tidak boleh ada jadwal yang tumpang tindih untuk ruangan yang sama
- Kapasitas ruangan harus mencukupi untuk jumlah mahasiswa
- Mata kuliah praktikum harus di ruangan praktikum
- Mata kuliah teori harus di ruangan kelas teori

### Soft Constraints (Diusahakan untuk dipenuhi)

- Preferensi waktu mengajar dosen
- Tidak ada jadwal kuliah pada waktu istirahat
- Distribusi kelas yang merata sepanjang minggu
- Jarak antar mata kuliah pada hari yang sama tidak terlalu jauh
- Jadwal mengajar dosen tidak tersebar ke banyak hari

## Algoritma Penjadwalan

### Algoritma Genetika

1. **Representasi Kromosom**: Kromosom direpresentasikan sebagai sekumpulan slot jadwal (mata kuliah, dosen, ruangan, waktu)
2. **Inisialisasi Populasi**: Membuat populasi awal dengan jadwal acak
3. **Fungsi Fitness**: Mengevaluasi kualitas jadwal berdasarkan jumlah constraint yang dipenuhi
4. **Seleksi**: Memilih kromosom dengan nilai fitness tinggi untuk reproduksi
5. **Crossover**: Menggabungkan dua kromosom induk untuk membentuk keturunan baru
6. **Mutasi**: Mengubah sebagian kecil dari kromosom secara acak
7. **Penggantian**: Populasi baru menggantikan populasi lama
8. **Kondisi Berhenti**: Proses berhenti setelah mencapai generasi maksimum atau threshold fitness tertentu

### Simulated Annealing

1. **Solusi Awal**: Menggunakan solusi terbaik dari Algoritma Genetika
2. **Temperatur Awal**: Menetapkan temperatur awal yang tinggi
3. **Fungsi Tetangga**: Membuat solusi tetangga dengan modifikasi kecil
4. **Fungsi Fitness**: Mengevaluasi kualitas solusi
5. **Probabilitas Penerimaan**: Menerima solusi yang lebih buruk dengan probabilitas tertentu
6. **Penurunan Temperatur**: Menurunkan temperatur secara bertahap
7. **Kondisi Berhenti**: Proses berhenti ketika temperatur mencapai nilai minimum atau tidak ada peningkatan

## Testing

### Unit Testing

- Pengujian komponen-komponen individu seperti fungsi algoritma, model data, dan tampilan

### Integration Testing

- Pengujian interaksi antar berbagai komponen sistem

### User Acceptance Testing (UAT)

- Pengujian oleh pengguna akhir (admin, dosen, mahasiswa)
- Metrik UAT:
  - Kegunaan (Usability)
  - Kepuasan pengguna (User satisfaction)

## Kontributor

Muhammad Fadhil Musyaffa - 2110511006
