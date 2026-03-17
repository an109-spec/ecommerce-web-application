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
│  │  ├─ review.py
│  │  ├─ shop.py
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
│  │  │  └─ __init__.py
│  │  ├─ promotion
│  │  │  ├─ flash_sale.py
│  │  │  ├─ routes.py
│  │  │  ├─ service.py
│  │  │  ├─ voucher.py
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
│  │  │  ├─ home.css
│  │  │  ├─ order.css
│  │  │  ├─ payment.css
│  │  │  ├─ product
│  │  │  │  ├─ filter.css
│  │  │  │  ├─ product_card.css
│  │  │  │  ├─ product_detail.css
│  │  │  │  ├─ product_list.css
│  │  │  │  └─ review.css
│  │  │  ├─ seller.css
│  │  │  └─ user.css
│  │  ├─ js
│  │  │  ├─ admin_dashboard.js
│  │  │  ├─ admin_orders.js
│  │  │  ├─ admin_products.js
│  │  │  ├─ audit.js
│  │  │  ├─ auth.js
│  │  │  ├─ base.js
│  │  │  ├─ cart.js
│  │  │  ├─ chat.js
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
│  │  │  │  └─ sort.js
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
│  │     └─ products
│  │        ├─ 0e21f405-f885-446c-9c46-c551e438f65b_shopping.avif
│  │        ├─ 687e55b2-eb6c-4af4-be50-7e6836afaa25_shopping.webp
│  │        ├─ 774926ac-d0d0-422a-8e6c-40b2d17bee58_shopping.avif
│  │        ├─ 7a4109e8-5d45-4bc0-bdb3-120da0cd7baf_shopping_3.webp
│  │        ├─ 7d20758b-1cd3-41cf-9111-e595ae699722_shopping_1.webp
│  │        ├─ 8816a3f3-24b6-46ba-87cd-973e5b77aadf_shopping_2.webp
│  │        ├─ a18e0156-41d7-4773-a331-95e2c974b044_shopping.avif
│  │        ├─ b41ebc24-4066-463a-a984-c38ec508f08e_download_2.jpg
│  │        ├─ df736ad9-34d0-44b8-89c4-f1b0fc094022_download_1.jpg
│  │        ├─ f1a5c5e2-4ab6-469c-adcb-e4b70a10b089_shopping.avif
│  │        └─ fcdaa36e-d7e0-4d1c-97b1-b5ba62e53329_download_2.jpg
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
│  │  │  └─ search.html
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
│  └─ __init__.py
├─ migrations
│  ├─ alembic.ini
│  ├─ env.py
│  ├─ README
│  ├─ script.py.mako
│  └─ versions
│     ├─ 00ee557e55bf_first_migration.py
│     ├─ 0d38f3b6dace_update_tables.py
│     ├─ 0eaad6ff6f52_merge_product_branches.py
│     ├─ 2dd5df952720_add_product_variants.py
│     ├─ 2f08041d1158_expand_otp_code_length.py
│     ├─ 3d109b001fb6_add_delivered_status.py
│     ├─ 41bf14fe284a_add_is_seller_column.py
│     ├─ 4e7ad61e46fa_refactor_product_schema.py
│     ├─ 5d8aad89768e_refactor_product_schema.py
│     ├─ 61b6f1b78bb3_refactor_product_variant_system.py
│     ├─ 8897eb48e61c_fix_timezone.py
│     ├─ a1b2c3d4e5f6_add_product_status_for_soft_delete.py
│     ├─ b2c3d4e5f6a7_add_seen_to_messages.py
│     ├─ c3d4e5f6a7b8_add_shop_description_and_shipping_fee.py
│     └─ fd941695ea87_fix_timezone.py
├─ PROJECT_OVERVIEW.md
├─ README.md
├─ requirements.txt
├─ run.py
└─ scripts
   └─ postgres_setup.sql

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
│  │  │  ├─ home.css
│  │  │  ├─ order.css
│  │  │  ├─ payment.css
│  │  │  ├─ product
│  │  │  │  ├─ filter.css
│  │  │  │  ├─ product_card.css
│  │  │  │  ├─ product_detail.css
│  │  │  │  ├─ product_list.css
│  │  │  │  └─ review.css
│  │  │  ├─ seller.css
│  │  │  ├─ seller_promotion.css
│  │  │  └─ user.css
│  │  ├─ js
│  │  │  ├─ admin_dashboard.js
│  │  │  ├─ admin_orders.js
│  │  │  ├─ admin_products.js
│  │  │  ├─ audit.js
│  │  │  ├─ auth.js
│  │  │  ├─ base.js
│  │  │  ├─ cart.js
│  │  │  ├─ chat.js
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
│  │     └─ products
│  │        ├─ 0e21f405-f885-446c-9c46-c551e438f65b_shopping.avif
│  │        ├─ 1144b200-78b8-4462-accc-28ae6e848fe7_download_2.jpg
│  │        ├─ 687e55b2-eb6c-4af4-be50-7e6836afaa25_shopping.webp
│  │        ├─ 774926ac-d0d0-422a-8e6c-40b2d17bee58_shopping.avif
│  │        ├─ 7a4109e8-5d45-4bc0-bdb3-120da0cd7baf_shopping_3.webp
│  │        ├─ 7d20758b-1cd3-41cf-9111-e595ae699722_shopping_1.webp
│  │        ├─ 8816a3f3-24b6-46ba-87cd-973e5b77aadf_shopping_2.webp
│  │        ├─ a18e0156-41d7-4773-a331-95e2c974b044_shopping.avif
│  │        ├─ b41ebc24-4066-463a-a984-c38ec508f08e_download_2.jpg
│  │        ├─ df736ad9-34d0-44b8-89c4-f1b0fc094022_download_1.jpg
│  │        ├─ f1a5c5e2-4ab6-469c-adcb-e4b70a10b089_shopping.avif
│  │        └─ fcdaa36e-d7e0-4d1c-97b1-b5ba62e53329_download_2.jpg
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
│  │  │  └─ search.html
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
├─ migrations
│  ├─ alembic.ini
│  ├─ env.py
│  ├─ README
│  ├─ script.py.mako
│  └─ versions
│     ├─ 00ee557e55bf_first_migration.py
│     ├─ 010828320975_add_shop_id_to_voucher.py
│     ├─ 0d38f3b6dace_update_tables.py
│     ├─ 0eaad6ff6f52_merge_product_branches.py
│     ├─ 1800151040e3_fix_timezone.py
│     ├─ 2dd5df952720_add_product_variants.py
│     ├─ 2f08041d1158_expand_otp_code_length.py
│     ├─ 3d109b001fb6_add_delivered_status.py
│     ├─ 41bf14fe284a_add_is_seller_column.py
│     ├─ 4e7ad61e46fa_refactor_product_schema.py
│     ├─ 5d8aad89768e_refactor_product_schema.py
│     ├─ 61b6f1b78bb3_refactor_product_variant_system.py
│     ├─ 794bf4a40444_add_timezone_to_promotion_datetime.py
│     ├─ 8897eb48e61c_fix_timezone.py
│     ├─ a1b2c3d4e5f6_add_product_status_for_soft_delete.py
│     ├─ b2c3d4e5f6a7_add_seen_to_messages.py
│     ├─ c3d4e5f6a7b8_add_shop_description_and_shipping_fee.py
│     ├─ e566b4974b95_fix_timezonee.py
│     ├─ fd941695ea87_fix_timezone.py
│     └─ fe9e636cee13_add_timezone_to_promotion_datetime.py
├─ PROJECT_OVERVIEW.md
├─ README.md
├─ requirements.txt
├─ run.py
└─ scripts
   └─ postgres_setup.sql

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
│  │  │  ├─ home.css
│  │  │  ├─ order.css
│  │  │  ├─ payment.css
│  │  │  ├─ product
│  │  │  │  ├─ filter.css
│  │  │  │  ├─ product_card.css
│  │  │  │  ├─ product_detail.css
│  │  │  │  ├─ product_list.css
│  │  │  │  └─ review.css
│  │  │  ├─ seller.css
│  │  │  ├─ seller_promotion.css
│  │  │  └─ user.css
│  │  ├─ js
│  │  │  ├─ admin_dashboard.js
│  │  │  ├─ admin_orders.js
│  │  │  ├─ admin_products.js
│  │  │  ├─ audit.js
│  │  │  ├─ auth.js
│  │  │  ├─ base.js
│  │  │  ├─ cart.js
│  │  │  ├─ chat.js
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
│  │     │  ├─ 0e21f405-f885-446c-9c46-c551e438f65b_shopping.avif
│  │     │  ├─ 1144b200-78b8-4462-accc-28ae6e848fe7_download_2.jpg
│  │     │  ├─ 687e55b2-eb6c-4af4-be50-7e6836afaa25_shopping.webp
│  │     │  ├─ 774926ac-d0d0-422a-8e6c-40b2d17bee58_shopping.avif
│  │     │  ├─ 7a4109e8-5d45-4bc0-bdb3-120da0cd7baf_shopping_3.webp
│  │     │  ├─ 7d20758b-1cd3-41cf-9111-e595ae699722_shopping_1.webp
│  │     │  ├─ 8816a3f3-24b6-46ba-87cd-973e5b77aadf_shopping_2.webp
│  │     │  ├─ a18e0156-41d7-4773-a331-95e2c974b044_shopping.avif
│  │     │  ├─ b41ebc24-4066-463a-a984-c38ec508f08e_download_2.jpg
│  │     │  ├─ df736ad9-34d0-44b8-89c4-f1b0fc094022_download_1.jpg
│  │     │  ├─ f1a5c5e2-4ab6-469c-adcb-e4b70a10b089_shopping.avif
│  │     │  └─ fcdaa36e-d7e0-4d1c-97b1-b5ba62e53329_download_2.jpg
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
│  │  │  └─ search.html
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
├─ migrations
│  ├─ alembic.ini
│  ├─ env.py
│  ├─ README
│  ├─ script.py.mako
│  └─ versions
│     ├─ 00ee557e55bf_first_migration.py
│     ├─ 010828320975_add_shop_id_to_voucher.py
│     ├─ 0d38f3b6dace_update_tables.py
│     ├─ 0eaad6ff6f52_merge_product_branches.py
│     ├─ 1800151040e3_fix_timezone.py
│     ├─ 2dd5df952720_add_product_variants.py
│     ├─ 2f08041d1158_expand_otp_code_length.py
│     ├─ 3d109b001fb6_add_delivered_status.py
│     ├─ 41bf14fe284a_add_is_seller_column.py
│     ├─ 4e7ad61e46fa_refactor_product_schema.py
│     ├─ 5d8aad89768e_refactor_product_schema.py
│     ├─ 61b6f1b78bb3_refactor_product_variant_system.py
│     ├─ 794bf4a40444_add_timezone_to_promotion_datetime.py
│     ├─ 8897eb48e61c_fix_timezone.py
│     ├─ a1b2c3d4e5f6_add_product_status_for_soft_delete.py
│     ├─ b2c3d4e5f6a7_add_seen_to_messages.py
│     ├─ c3d4e5f6a7b8_add_shop_description_and_shipping_fee.py
│     ├─ e566b4974b95_fix_timezonee.py
│     ├─ fd941695ea87_fix_timezone.py
│     └─ fe9e636cee13_add_timezone_to_promotion_datetime.py
├─ PROJECT_OVERVIEW.md
├─ README.md
├─ requirements.txt
├─ run.py
└─ scripts
   └─ postgres_setup.sql

```