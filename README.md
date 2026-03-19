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

```
DO_AN_TOT_NGHIEP
├─ app
│  ├─ cli.py
│  ├─ common
│  │  ├─ constants.py
│  │  ├─ decorators.py
│  │  ├─ exceptions.py
│  │  ├─ security
│  │  │  ├─ otp.py
│  │  │  ├─ password.py
│  │  │  ├─ permission.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ config
│  │  ├─ config.py
│  │  └─ __init__.py
│  ├─ core
│  │  └─ enums
│  │     ├─ order_status.py
│  │     └─ product_status.py
│  ├─ extensions
│  │  ├─ db.py
│  │  ├─ jwt.py
│  │  ├─ mail.py
│  │  ├─ socketio.py
│  │  └─ __init__.py
│  ├─ models
│  │  ├─ audit_log.py
│  │  ├─ base.py
│  │  ├─ cart.py
│  │  ├─ chat.py
│  │  ├─ flash_sale.py
│  │  ├─ order.py
│  │  ├─ otp.py
│  │  ├─ payment.py
│  │  ├─ product.py
│  │  ├─ promotion.py
│  │  ├─ review.py
│  │  ├─ shop.py
│  │  ├─ shop_follow.py
│  │  ├─ user.py
│  │  ├─ voucher.py
│  │  ├─ wishlist.py
│  │  └─ __init__.py
│  ├─ modules
│  │  ├─ admin
│  │  │  ├─ analytics.py
│  │  │  ├─ dashboard.py
│  │  │  ├─ order_manager.py
│  │  │  ├─ product_manager.py
│  │  │  ├─ routes.py
│  │  │  ├─ user_manager.py
│  │  │  └─ __init__.py
│  │  ├─ audit
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  └─ __init__.py
│  │  ├─ auth
│  │  │  ├─ dto.py
│  │  │  ├─ email_service.py
│  │  │  ├─ mail_service.py
│  │  │  ├─ otp_service.py
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  ├─ sms_service.py
│  │  │  ├─ validators.py
│  │  │  └─ __init__.py
│  │  ├─ cart
│  │  │  ├─ calculator.py
│  │  │  ├─ dto.py
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  └─ __init__.py
│  │  ├─ chat
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  ├─ socket.py
│  │  │  └─ __init__.py
│  │  ├─ checkout
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  └─ __init__.py
│  │  ├─ home
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  └─ __init__.py
│  │  ├─ order
│  │  │  ├─ dto.py
│  │  │  ├─ exporter.py
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  ├─ status.py
│  │  │  ├─ tracking.py
│  │  │  ├─ workflow.py
│  │  │  └─ __init__.py
│  │  ├─ payment
│  │  │  ├─ dto.py
│  │  │  ├─ gateway.py
│  │  │  ├─ methods.py
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  └─ __init__.py
│  │  ├─ product
│  │  │  ├─ dto.py
│  │  │  ├─ filters.py
│  │  │  ├─ inventory.py
│  │  │  ├─ qr_service.py
│  │  │  ├─ routes.py
│  │  │  ├─ search.py
│  │  │  ├─ service.py
│  │  │  ├─ shop_service.py
│  │  │  └─ __init__.py
│  │  ├─ promotion
│  │  │  ├─ repository.py
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  └─ __init__.py
│  │  ├─ seller
│  │  │  ├─ center_service.py
│  │  │  ├─ dto.py
│  │  │  ├─ order_manager.py
│  │  │  ├─ product_manager.py
│  │  │  ├─ product_service.py
│  │  │  ├─ repository.py
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  └─ __init__.py
│  │  └─ user
│  │     ├─ routes.py
│  │     ├─ service.py
│  │     └─ __init__.py
│  ├─ static
│  │  ├─ css
│  │  │  ├─ admin.css
│  │  │  ├─ auth.css
│  │  │  ├─ base.css
│  │  │  ├─ cart.css
│  │  │  ├─ chat.css
│  │  │  ├─ checkout.css
│  │  │  ├─ home.css
│  │  │  ├─ order.css
│  │  │  ├─ payment.css
│  │  │  ├─ product
│  │  │  │  ├─ filter.css
│  │  │  │  ├─ product_card.css
│  │  │  │  ├─ product_detail.css
│  │  │  │  ├─ product_list.css
│  │  │  │  ├─ review.css
│  │  │  │  └─ shop_public.css
│  │  │  ├─ seller.css
│  │  │  ├─ seller_promotion.css
│  │  │  └─ user.css
│  │  ├─ images
│  │  │  └─ no-image.png
│  │  ├─ js
│  │  │  ├─ admin_dashboard.js
│  │  │  ├─ admin_orders.js
│  │  │  ├─ admin_products.js
│  │  │  ├─ audit.js
│  │  │  ├─ auth.js
│  │  │  ├─ base.js
│  │  │  ├─ cart.js
│  │  │  ├─ chat.js
│  │  │  ├─ checkout.js
│  │  │  ├─ home.js
│  │  │  ├─ order.js
│  │  │  ├─ payment.js
│  │  │  ├─ product
│  │  │  │  ├─ filter.js
│  │  │  │  ├─ product_detail.js
│  │  │  │  ├─ product_list.js
│  │  │  │  ├─ qr.js
│  │  │  │  ├─ review.js
│  │  │  │  ├─ search.js
│  │  │  │  ├─ shop_public.js
│  │  │  │  └─ sort.js
│  │  │  ├─ promotion
│  │  │  │  ├─ flash_sale.js
│  │  │  │  ├─ flash_sale_ui.js
│  │  │  │  ├─ promotion_common.js
│  │  │  │  └─ voucher.js
│  │  │  ├─ seller.js
│  │  │  └─ user.js
│  │  └─ uploads
│  │     ├─ avatars
│  │     │  ├─ 2721bfa8b2424a6e83dc1f3b27589034-eed2bf11ff458085bddcb1ba46741e09.jpg
│  │     │  ├─ 3dfb3185a64e47609e0f2b6b4f1b7395-bf88d3f5c61052a917a29560582d3b081.jpg
│  │     │  ├─ 898686e903c0456e996f8e868d09c68a-7a8211a2161799550aa868aaab6d5c84.jpg
│  │     │  ├─ 9741a4421b5a4d198494a4fdd17a1fcc-7a8211a2161799550aa868aaab6d5c84.jpg
│  │     │  ├─ a5c053e1e88143b5bac0d9bdfe0b00bb-7a8211a2161799550aa868aaab6d5c84.jpg
│  │     │  └─ e1f4897aaa3140e48a5cdfdb07031ec3-7a8211a2161799550aa868aaab6d5c84.jpg
│  │     ├─ products
│  │     │  ├─ 0616b194-9992-4fed-8b7e-3a2bac11fdeb_vn-11134207-7ras8-md91oowkzq70f3.webp
│  │     │  ├─ 1144b200-78b8-4462-accc-28ae6e848fe7_download_2.jpg
│  │     │  ├─ 13eca1f7-6ea3-48dd-8093-77034fe75cdd_shopping.avif
│  │     │  ├─ 226a69d0-0987-43c8-ae80-e04bda731de1_vn-11134207-820l4-mix95h41x05fa8resize_w450_nl.webp
│  │     │  ├─ 26f6c544-81e5-46a6-bbf7-8d8b739451f9_sg-11134201-7rd4h-m7vwf90se7c716.webp
│  │     │  ├─ 2d4c8657-4285-4e69-8b1a-92ed8a23472d_sg-11134201-7rd6o-m7vwf7maepkzaf.webp
│  │     │  ├─ 2eae0327-735e-4f43-9dc9-68b3442d47e4_vn-11134207-820l4-mix7vi6w07wh0fresize_w450_nl.webp
│  │     │  ├─ 2f3d5ce9-b0df-4979-98ab-79125cb71289_vn-11134207-820l4-mhng2xbmswzl15resize_w450_nl.webp
│  │     │  ├─ 38ff736b-dd8a-4450-83ea-1521ea650479_shopping.avif
│  │     │  ├─ 40774bc8-6a1f-4fcd-babe-6e403dfe1657_vn-11134207-7ras8-md91oowkzq70f3.webp
│  │     │  ├─ 40989404-b361-4fbf-8f8d-d3cf56c59121_vn-11134207-7ras8-md91f6y1ai5824.webp
│  │     │  ├─ 43dd7e02-6707-4769-928e-32552fce6133_sg-11134201-7rd6o-m7vwf7maepkzaf.webp
│  │     │  ├─ 4574e73e-594b-44b8-9273-e154e056b60a_vn-11134207-7ras8-md91f6y1ai5824.webp
│  │     │  ├─ 464866d4-9471-4ee6-bfdc-89544ab641f2_sg-11134201-7rd57-m7vwf8a5ik1d85.webp
│  │     │  ├─ 4927cf98-d23b-47f9-924c-7ec961edb262_vn-11134207-820l4-mhng36zhm6md8aresize_w450_nl.webp
│  │     │  ├─ 55d1fa3c-bb17-4bf1-b725-a5c1f1b7b82e_sg-11134201-7rd4h-m7vwf90se7c716.webp
│  │     │  ├─ 584b2cbd-6039-4412-958b-95564199d2a5_sg-11134201-7rd57-m7vwf8a5ik1d85.webp
│  │     │  ├─ 687e55b2-eb6c-4af4-be50-7e6836afaa25_shopping.webp
│  │     │  ├─ 6bdb26eb-20a0-4e79-9831-c05261b246a9_vn-11134207-820l4-mhng2xbmswzl15resize_w450_nl.webp
│  │     │  ├─ 7334137c-0eb0-400b-8184-9f3379e7ea2a_download_2.jpg
│  │     │  ├─ 774926ac-d0d0-422a-8e6c-40b2d17bee58_shopping.avif
│  │     │  ├─ 7a4109e8-5d45-4bc0-bdb3-120da0cd7baf_shopping_3.webp
│  │     │  ├─ 7d20758b-1cd3-41cf-9111-e595ae699722_shopping_1.webp
│  │     │  ├─ 807d915d-74df-4845-be75-c0a5e6add7e6_download_2.jpg
│  │     │  ├─ 8816a3f3-24b6-46ba-87cd-973e5b77aadf_shopping_2.webp
│  │     │  ├─ 89aeae84-f4d5-4b52-9f25-ce3a856766e7_sg-11134201-7rd4h-m7vwf90se7c716.webp
│  │     │  ├─ 8aba2790-cb2b-4187-bffb-8ee431912e7c_vn-11134207-820l4-mhng2xbmswzl15resize_w450_nl.webp
│  │     │  ├─ 8b87683b-0c92-47c6-95b7-9be3262e1889_download_2.jpg
│  │     │  ├─ 9149bc50-578d-4eaa-842c-8e55f9edea34_sg-11134201-7rd4h-m7vwf90se7c716.webp
│  │     │  ├─ 922fe0d3-7383-46c7-a120-8c1e2e04e2c9_sg-11134201-7rd6g-m7vwf7zbvklwd5.webp
│  │     │  ├─ 94879487-a1bf-4871-a059-61bf4fc4f18f_sg-11134201-7rd6g-m7vwf7zbvklwd5.webp
│  │     │  ├─ 988acde5-b229-4682-8e95-037e566a4d5d_sg-11134201-7rd4h-m7vwf90se7c716.webp
│  │     │  ├─ ab8c756a-64ba-4527-ab67-69f62082c5a7_sg-11134201-7rd6g-m7vwf7zbvklwd5.webp
│  │     │  ├─ b280a575-1a36-44a7-bf8c-e26057739363_sg-11134201-7rd57-m7vwf8a5ik1d85.webp
│  │     │  ├─ b425f6b9-5dec-4b1e-ac8d-f3279a90b9ea_sg-11134201-7rd6o-m7vwf7maepkzaf.webp
│  │     │  ├─ b60fe2d7-d47c-4d3b-bf75-3df1863e9418_vn-11134207-820l4-mix95h41x05fa8resize_w450_nl.webp
│  │     │  ├─ bda24507-4c1f-4964-8789-1f1081f32a9e_sg-11134201-7rd57-m7vwf8a5ik1d85.webp
│  │     │  ├─ c9cda31f-3453-46d3-9a84-98956bfd09b8_vn-11134201-820l4-mff34lb00xzi8d.webp
│  │     │  ├─ ce13adac-5a2d-4e2c-b793-59ac04c2e362_vn-11134207-820l4-mhng36zhm6md8aresize_w450_nl.webp
│  │     │  ├─ df736ad9-34d0-44b8-89c4-f1b0fc094022_download_1.jpg
│  │     │  ├─ e1a7eb80-0c6e-4d40-8a83-a2ff09d83f8f_vn-11134207-7ras8-md91f6y1ai5824.webp
│  │     │  ├─ e92b25a5-e911-4040-86f0-cd0889436b4c_sg-11134201-7rd6g-m7vwf7zbvklwd5.webp
│  │     │  ├─ edea6293-b62e-4751-be87-b72dfc66e788_sg-11134201-7rd6o-m7vwf7maepkzaf.webp
│  │     │  ├─ f0020aa3-8309-4866-8852-32c3dd20fe46_sg-11134201-7rd6g-m7vwf7zbvklwd5.webp
│  │     │  ├─ f1df5b56-bc32-425d-962a-bd96508872dd_vn-11134207-820l4-mix7vi6w07wh0fresize_w450_nl.webp
│  │     │  └─ f65ac86b-7d5d-4530-beaa-d0249a2d6db6_sg-11134201-7rd4h-m7vwf90se7c716.webp
│  │     └─ shops
│  │        └─ 055e3034-8237-4623-95ff-d0ce08fb679c_3ac0031867ef212e4c2329fe9028fca1.jpg
│  ├─ templates
│  │  ├─ admin
│  │  │  ├─ analytics.html
│  │  │  ├─ dashboard.html
│  │  │  ├─ layout_admin.html
│  │  │  ├─ orders.html
│  │  │  ├─ products.html
│  │  │  └─ users.html
│  │  ├─ audit
│  │  │  └─ audit_log.html
│  │  ├─ auth
│  │  │  ├─ forgot_password.html
│  │  │  ├─ login.html
│  │  │  ├─ register.html
│  │  │  ├─ reset_password.html
│  │  │  └─ verify_otp.html
│  │  ├─ cart
│  │  │  ├─ cart.html
│  │  │  ├─ _cart_item.html
│  │  │  └─ _cart_summary.html
│  │  ├─ chat
│  │  │  └─ chat.html
│  │  ├─ checkout
│  │  │  └─ index.html
│  │  ├─ home
│  │  │  ├─ index.html
│  │  │  └─ support.html
│  │  ├─ layouts
│  │  │  └─ base.html
│  │  ├─ order
│  │  │  ├─ admin
│  │  │  │  ├─ admin_order_detail.html
│  │  │  │  ├─ admin_order_list.html
│  │  │  │  └─ admin_order_update_status.html
│  │  │  ├─ components
│  │  │  │  ├─ order_item_table.html
│  │  │  │  ├─ order_status_badge.html
│  │  │  │  ├─ order_timeline.html
│  │  │  │  └─ tracking_progress.html
│  │  │  └─ user
│  │  │     ├─ order_detail.html
│  │  │     ├─ order_list.html
│  │  │     └─ tracking.html
│  │  ├─ payment
│  │  │  ├─ payment_qr.html
│  │  │  ├─ payment_success.html
│  │  │  └─ select_payment.html
│  │  ├─ product
│  │  │  ├─ components
│  │  │  │  ├─ product_card.html
│  │  │  │  ├─ product_filter.html
│  │  │  │  ├─ product_sort.html
│  │  │  │  ├─ qr_modal.html
│  │  │  │  └─ review_item.html
│  │  │  ├─ detail.html
│  │  │  ├─ list.html
│  │  │  ├─ search.html
│  │  │  └─ shop_public.html
│  │  ├─ promotion
│  │  │  ├─ flash_sale.html
│  │  │  └─ voucher_list.html
│  │  ├─ seller
│  │  │  ├─ chat.html
│  │  │  ├─ dashboard.html
│  │  │  ├─ layout_seller.html
│  │  │  ├─ layout_seller_register.html
│  │  │  ├─ order
│  │  │  │  ├─ order_detail.html
│  │  │  │  └─ order_list.html
│  │  │  ├─ product
│  │  │  │  ├─ product_create.html
│  │  │  │  ├─ product_detail.html
│  │  │  │  ├─ product_edit.html
│  │  │  │  └─ product_list.html
│  │  │  ├─ promotion
│  │  │  │  ├─ flash_sale_create.html
│  │  │  │  ├─ flash_sale_edit.html
│  │  │  │  ├─ flash_sale_list.html
│  │  │  │  ├─ promotion_create.html
│  │  │  │  ├─ promotion_edit.html
│  │  │  │  ├─ promotion_list.html
│  │  │  │  ├─ voucher_create.html
│  │  │  │  ├─ voucher_edit.html
│  │  │  │  └─ voucher_list.html
│  │  │  ├─ promotions.html
│  │  │  ├─ revenue.html
│  │  │  └─ shop
│  │  │     ├─ complete.html
│  │  │     ├─ register_shop.html
│  │  │     ├─ settings.html
│  │  │     ├─ shipping_setup.html
│  │  │     ├─ shop_edit.html
│  │  │     └─ shop_profile.html
│  │  └─ user
│  │     └─ center.html
│  ├─ utils
│  │  └─ time.py
│  └─ __init__.py
├─ backup.dump
├─ migrations
│  ├─ alembic.ini
│  ├─ env.py
│  ├─ README
│  ├─ script.py.mako
│  └─ versions
│     └─ d6a64cb4d339_fix_timezone.py
├─ PROJECT_OVERVIEW.md
├─ README.md
├─ requirements.txt
├─ run.py
└─ scripts
   └─ postgres_setup.sql

```