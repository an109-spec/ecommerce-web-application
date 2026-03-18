📌 Mô tả dự án (Description)
**Shopee Mini Backend** là hệ thống backend RESTful API mô phỏng các chức năng cốt lõi của một sàn thương mại điện tử, phục vụ cho đồ án tốt nghiệp.
Dự án tập trung vào việc xây dựng các API quản lý người dùng, xác thực – phân quyền, sản phẩm, đơn hàng và các nghiệp vụ liên quan, tuân theo kiến trúc backend hiện đại.
Hệ thống được thiết kế theo mô hình **client–server**, tách biệt frontend và backend, dễ mở rộng, dễ bảo trì và sẵn sàng tích hợp với các ứng dụng web hoặc mobile.
---

## 🛠 Công nghệ sử dụng
- **Python 3**
- **Flask** – Web framework
- **Flask SQLAlchemy** – ORM thao tác cơ sở dữ liệu
- **Flask-JWT-Extended** – Xác thực & phân quyền bằng JWT
- **Flask-Migrate** – Quản lý migration database
- **Flask-Mail** – Gửi email
- **MySQL / PostgreSQL**
- **Git & GitHub** – Quản lý source code
---

## ⚙️ Chức năng chính
- Đăng ký / đăng nhập người dùng
- Xác thực & phân quyền (JWT)
- Quản lý người dùng
- Quản lý sản phẩm
- Quản lý đơn hàng
- Theo dõi trạng thái đơn hàng
- API phục vụ frontend / mobile app

---
## 🚀 Hướng dẫn chạy dự án

### 1️⃣ Clone repository
git clone https://github.com/an109-spec/shopee-mini-backend.git
cd shopee-mini-backend

### 2️⃣ Tạo virtual environment
python -m venv venv
source venv/bin/activate # Linux / Mac
venv\Scripts\activate # Windows

### 3️⃣ Cài đặt thư viện
pip install -r requirements.txt

### 4️⃣ Tạo file `.env`
```env
FLASK_ENV=development
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
DATABASE_URL=your_database_url
```

### 5️⃣ Chạy ứng dụng
python run.py
API mặc định chạy tại:
http://127.0.0.1:5000
## 📁 Cấu trúc thư mục

```
DO_AN_TOT_NGHIEP/
│── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── extensions/
│   └── __init__.py
│── run.py
│── requirements.txt
│── .gitignore
│── README.md
```

## 🎯 Mục tiêu đồ án
- Áp dụng kiến thức Backend Web vào dự án thực tế
- Nắm vững RESTful API, JWT, ORM
- Rèn luyện quy trình làm việc với Git/GitHub
- Sẵn sàng mở rộng thành hệ thống thương mại điện tử hoàn chỉnh

---

## 🐘 Thiết lập PostgreSQL và tạo CSDL đầy đủ

Bạn có thể chạy project bằng SQLite (mặc định), nhưng để dùng PostgreSQL thì làm theo các bước sau.

### 1) Cài PostgreSQL
- Ubuntu/Debian: `sudo apt update && sudo apt install postgresql postgresql-contrib`
- Windows: cài bằng installer từ trang PostgreSQL
- macOS: `brew install postgresql@16`

### 2) Cấu hình thông tin DB trong `.env`
Bạn có thể copy nhanh từ file mẫu:

```bash
cp .env.example .env
```

Thêm các biến bootstrap PostgreSQL vào `.env`:

```env
APP_DB_USER=your_db_user
APP_DB_PASSWORD=your_db_password
APP_DB_NAME=shopee_mini
```

### 3) Tạo user/database từ `.env` (không cần truyền `-v`)

```bash
set -a && source .env && set +a
sudo -E -u postgres psql -f scripts/postgres_setup.sql
```

Script sẽ tự đọc `APP_DB_USER`, `APP_DB_PASSWORD`, `APP_DB_NAME` từ environment.

### 4) Cấu hình URL kết nối ứng dụng
Tạo/cập nhật `.env`:

```env
FLASK_ENV=development
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://your_db_user:your_db_password@localhost:5432/shopee_mini
```

### 5) Cài dependency PostgreSQL driver

```bash
pip install psycopg2-binary
```

### 6) Tạo toàn bộ bảng từ models
Repo đã có lệnh CLI `init-db`:

```bash
flask --app run.py init-db
```

Nếu muốn reset và tạo lại toàn bộ bảng:

```bash
flask --app run.py init-db --drop
```

### 7) Chạy ứng dụng

```bash
python run.py
```

> Gợi ý: sau khi tạo DB xong, hãy đăng ký user đầu tiên tại `/auth/register`,
> rồi vào `/user/center` để test profile/avatar/password/purchase-history.
```
