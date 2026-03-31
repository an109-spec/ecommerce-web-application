"""seed_categories

Revision ID: 3106605f95cd
Revises: 011fd4441050
Create Date: 2026-03-31 09:15:16.599693

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3106605f95cd'
down_revision = '011fd4441050'
branch_labels = None
depends_on = None


CATEGORY_GROUPS = {
    "Công nghệ & Phụ kiện số": [
        "Máy tính bảng",
        "Đồng hồ thông minh",
        "Màn hình máy tính",
        "Chuột máy tính",
        "Bàn phím cơ",
        "Ổ cứng di động",
        "Thiết bị phát Wi-Fi",
        "Phụ kiện điện thoại",
    ],
    "Điện tử & Âm thanh - Hình ảnh": [
        "Máy ảnh kỹ thuật số",
        "Máy quay phim",
        "Loa Bluetooth",
        "Thiết bị âm thanh & Loa",
    ],
    "Điện máy & Gia dụng": [
        "Tủ lạnh",
        "Máy giặt",
        "Máy hút bụi",
        "Máy lọc không khí",
        "Máy sấy tóc",
        "Thiết bị gia dụng",
    ],
    "Thiết bị Nhà bếp": [
        "Nồi chiên không dầu",
        "Lò vi sóng",
        "Thiết bị nhà bếp",
    ],
    "Thời trang & Phụ kiện cá nhân": [
        "Thời trang trẻ em",
        "Giày dép nam",
        "Giày dép nữ",
        "Giày thể thao",
        "Giày cao gót",
        "Túi xách nữ",
        "Balo du lịch",
        "Túi xách & Balo",
        "Kính mát",
        "Đồng hồ & Trang sức",
    ],
    "Sức khỏe & Làm đẹp": [
        "Mỹ phẩm Hàn Quốc",
        "Kem chống nắng",
        "Nước hoa",
        "Nước hoa & Nến thơm",
        "Chăm sóc sức khỏe",
    ],
    "Thể thao & Đời sống": [
        "Dụng cụ tập Gym",
        "Thảm tập Yoga",
        "Thể thao & Dã ngoại",
        "Chăm sóc thú cưng",
        "Ô tô & Xe máy",
    ],
    "Nội thất & Đồ chơi - Sở thích": [
        "Nội thất & Trang trí nhà",
        "Đồ chơi mô hình",
        "Đồ chơi & Mô hình",
    ],
    "Sách & Văn phòng phẩm": [
        "Văn phòng phẩm",
        "Sách kỹ năng",
        "Sách & Văn phòng phẩm",
    ],
}


def _ensure_category(conn, name: str, parent_id: int | None) -> int:
    # 1. Kiểm tra xem category đã tồn tại chưa
    row = conn.execute(
        sa.text("SELECT id FROM categories WHERE name = :name LIMIT 1"),
        {"name": name},
    ).fetchone()

    if row:
        # Nếu tồn tại rồi thì chỉ cập nhật parent_id
        conn.execute(
            sa.text("UPDATE categories SET parent_id = :parent_id WHERE id = :id"),
            {"parent_id": parent_id, "id": row[0]},
        )
        return int(row[0])

    # 2. Nếu chưa tồn tại, chèn mới (CHỈ chèn name và parent_id)
    inserted = conn.execute(
        sa.text(
            """
            INSERT INTO categories (name, parent_id, created_at)
            VALUES (:name, :parent_id, NOW())
            RETURNING id
            """
        ),
        {"name": name, "parent_id": parent_id},
    ).fetchone()
    return int(inserted[0])

def upgrade() -> None:
    conn = op.get_bind()
    for parent_name, children in CATEGORY_GROUPS.items():
        parent_id = _ensure_category(conn, parent_name, None)
        for child_name in children:
            _ensure_category(conn, child_name, parent_id)


def downgrade() -> None:
    conn = op.get_bind()
    child_names = [child for children in CATEGORY_GROUPS.values() for child in children]
    parent_names = list(CATEGORY_GROUPS.keys())
    for child_name in child_names:
        conn.execute(sa.text("DELETE FROM categories WHERE name = :name"), {"name": child_name})
    for parent_name in parent_names:
        conn.execute(sa.text("DELETE FROM categories WHERE name = :name"), {"name": parent_name})