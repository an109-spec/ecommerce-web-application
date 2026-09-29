# E-commerce Web Application

## 📌 Giới thiệu

**E-commerce Web Application** là dự án cá nhân mô phỏng một hệ thống thương mại điện tử, được xây dựng để áp dụng kiến thức về phát triển ứng dụng web và cơ sở dữ liệu.

Dự án tập trung vào các chức năng chính như quản lý người dùng, sản phẩm, đơn hàng và xác thực tài khoản.

## 🛠 Công nghệ sử dụng

* **Python 3**
* **Flask**
* **Flask SQLAlchemy**
* **Flask-JWT-Extended**
* **Flask-Migrate**
* **Flask-Mail**
* **MySQL / PostgreSQL**

## ⚙️ Chức năng chính

* Đăng ký / đăng nhập người dùng
* Xác thực và phân quyền
* Quản lý người dùng
* Quản lý sản phẩm
* Quản lý đơn hàng
* Theo dõi trạng thái đơn hàng
* RESTful API phục vụ ứng dụng web

## 📁 Cấu trúc dự án

```text
project/
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── extensions/
│   └── __init__.py
├── run.py
├── requirements.txt
├── .gitignore
└── README.md
```

## 🚀 Cài đặt và chạy

### 1. Clone repository

```bash
git clone https://github.com/an109-spec/shopee-mini-backend.git
cd shopee-mini-backend
```

### 2. Tạo môi trường ảo

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình môi trường

Tạo file `.env`:

```env
FLASK_ENV=development
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
DATABASE_URL=your_database_url
```

### 5. Khởi chạy ứng dụng

```bash
python run.py
```

Ứng dụng mặc định chạy tại:

```text
http://127.0.0.1:5000
```

## 🎯 Mục tiêu dự án

* Áp dụng kiến thức phát triển ứng dụng web vào một dự án hoàn chỉnh.
* Làm quen với RESTful API, xác thực người dùng và cơ sở dữ liệu.
* Rèn luyện khả năng phân tích yêu cầu và xây dựng các chức năng của hệ thống.

## 📝 Ghi chú

Dự án được thực hiện với mục đích học tập và xây dựng portfolio cá nhân.
