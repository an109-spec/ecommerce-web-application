from datetime import date
from decimal import Decimal
from hashlib import sha256
from urllib.parse import urlparse
import json
import requests
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash
from uuid import uuid4
from app.common.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
    AppException,
)
from app.extensions import db
from app.models import Order, OrderItem, Product, User, UserProfile


class UserService:
    AVATAR_STYLES = ("avataaars", "bottts", "identicon", "micah", "notionists")
    ADDRESS_SOURCE_URL = "https://provinces.open-api.vn/api"

    # ==============================
    # INTERNAL HELPERS
    # ==============================

    @staticmethod
    def _get_user(user_id: int) -> User:
        try:
            user = db.session.get(User, user_id)
        except SQLAlchemyError:
            raise AppException("Lỗi hệ thống cơ sở dữ liệu", status_code=500)

        if not user:
            raise NotFoundError("Không tìm thấy người dùng")

        return user

    @staticmethod
    def _decimal_to_string(value: Decimal | None) -> str:
        if value is None:
            return "0"
        return str(value)

    @staticmethod
    def _validate_avatar_url(avatar_url: str) -> str:
        if not avatar_url or not avatar_url.strip():
            raise ValidationError("Avatar không được để trống")

        avatar_url = avatar_url.strip()

        if len(avatar_url) > 500:
            raise ValidationError("URL avatar quá dài")

        parsed = urlparse(avatar_url)

        if parsed.scheme not in {"http", "https"}:
            raise ValidationError("Avatar phải dùng http hoặc https")

        if not parsed.netloc:
            raise ValidationError("Avatar phải là URL hợp lệ")

        if not parsed.path.lower().endswith(
            (".png", ".jpg", ".jpeg", ".webp", ".svg")
        ):
            raise ValidationError("Avatar phải là file ảnh hợp lệ")

        return avatar_url

    @staticmethod
    def change_avatar(user_id: int, avatar_url: str) -> str:
        avatar_url = UserService._validate_avatar_url(avatar_url)
        user = UserService._get_user(user_id)
        user.avatar = avatar_url
        db.session.commit()

        return avatar_url
    # ==============================
    # PROFILE
    # ==============================

    @staticmethod
    def get_profile(user_id: int) -> dict:
        user = UserService._get_user(user_id)
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        addresses = UserService._load_addresses(profile.address if profile else None)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "avatar": user.avatar,
            "role": user.role,
            "profile": {
                "full_name": profile.full_name if profile else None,
                "address": profile.address if profile else None,
                "addresses": addresses,
                "gender": profile.gender if profile else None,
                "birthday": profile.birthday.isoformat() if profile and profile.birthday else None,
            },
        }
    @staticmethod
    def _load_addresses(raw_value: str | None) -> list[dict]:
        if not raw_value:
            return []

        try:
            parsed = json.loads(raw_value)
            if isinstance(parsed, list):
                normalized = []
                for item in parsed:
                    if not isinstance(item, dict):
                        continue
                    normalized.append(
                        {
                            "id": str(item.get("id") or uuid4().hex),
                            "full_name": str(item.get("full_name") or "").strip(),
                            "phone": str(item.get("phone") or "").strip(),
                            "city": str(item.get("city") or "").strip(),
                            "district": str(item.get("district") or "").strip(),
                            "ward": str(item.get("ward") or "").strip(),
                            "address_line": str(item.get("address_line") or "").strip(),
                            "is_default": bool(item.get("is_default", False)),
                        }
                    )
                if any(i["is_default"] for i in normalized):
                    first_default = next(i for i in normalized if i["is_default"])
                    for item in normalized:
                        item["is_default"] = item["id"] == first_default["id"]
                elif normalized:
                    normalized[0]["is_default"] = True
                return normalized
        except (TypeError, json.JSONDecodeError):
            pass

        legacy = [item.strip() for item in raw_value.split("\n") if item.strip()]
        return [
            {
                "id": uuid4().hex,
                "full_name": "",
                "phone": "",
                "city": "",
                "district": "",
                "ward": "",
                "address_line": line,
                "is_default": idx == 0,
            }
            for idx, line in enumerate(legacy)
        ]

    @staticmethod
    def _save_addresses(profile: UserProfile, addresses: list[dict]) -> None:
        profile.address = json.dumps(addresses, ensure_ascii=False)
    
    @staticmethod
    def _fetch_address_json(path: str) -> dict | list:
        try:
            response = requests.get(f"{UserService.ADDRESS_SOURCE_URL}{path}", timeout=8)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            raise AppException("Không thể tải dữ liệu địa chỉ", status_code=503)

    @staticmethod
    def list_provinces() -> list[dict]:
        data = UserService._fetch_address_json("/p/")
        if not isinstance(data, list):
            return []
        return [
            {"code": str(item.get("code")), "name": str(item.get("name") or "").strip()}
            for item in data
            if isinstance(item, dict) and item.get("code") is not None
        ]

    @staticmethod
    def list_districts(province_code: str) -> list[dict]:
        if not province_code:
            raise ValidationError("Thiếu mã Tỉnh/Thành phố")
        data = UserService._fetch_address_json(f"/p/{province_code}?depth=2")
        districts = data.get("districts", []) if isinstance(data, dict) else []
        return [
            {"code": str(item.get("code")), "name": str(item.get("name") or "").strip()}
            for item in districts
            if isinstance(item, dict) and item.get("code") is not None
        ]

    @staticmethod
    def list_wards(district_code: str) -> list[dict]:
        if not district_code:
            raise ValidationError("Thiếu mã Quận/Huyện")
        data = UserService._fetch_address_json(f"/d/{district_code}?depth=2")
        wards = data.get("wards", []) if isinstance(data, dict) else []
        return [
            {"code": str(item.get("code")), "name": str(item.get("name") or "").strip()}
            for item in wards
            if isinstance(item, dict) and item.get("code") is not None
        ]

    @staticmethod
    def update_profile(user_id: int, payload: dict) -> dict:
        user = UserService._get_user(user_id)
        profile = UserProfile.query.filter_by(user_id=user.id).first()

        if profile is None:
            profile = UserProfile(user_id=user.id)
            db.session.add(profile)

        username = (payload.get("username") or "").strip()
        email = (payload.get("email") or "").strip().lower()
        phone = (payload.get("phone") or "").strip()
        full_name = (payload.get("full_name") or "").strip()
        birthday_raw = (payload.get("birthday") or "").strip()
        addresses_provided = "addresses" in payload
        addresses = payload.get("addresses") if addresses_provided else None

        if username:
            conflict = User.query.filter(User.username == username, User.id != user.id).first()
            if conflict:
                raise ConflictError("Username đã tồn tại")
            user.username = username

        if email:
            conflict = User.query.filter(User.email == email, User.id != user.id).first()
            if conflict:
                raise ConflictError("Email đã tồn tại")
            user.email = email

        if phone:
            conflict = User.query.filter(User.phone == phone, User.id != user.id).first()
            if conflict:
                raise ConflictError("Số điện thoại đã tồn tại")
            user.phone = phone

        if full_name:
            profile.full_name = full_name

        if birthday_raw:
            try:
                profile.birthday = date.fromisoformat(birthday_raw)
            except ValueError:
                raise ValidationError("Ngày sinh không hợp lệ, dùng định dạng YYYY-MM-DD")

        if addresses_provided:
            if not isinstance(addresses, list):
                raise ValidationError("Danh sách địa chỉ không hợp lệ")
            cleaned = []
            for item in addresses:
                if isinstance(item, dict):
                    cleaned.append(item)
                elif str(item).strip():
                    cleaned.append(
                        {
                            "id": uuid4().hex,
                            "full_name": "",
                            "phone": "",
                            "city": "",
                            "district": "",
                            "ward": "",
                            "address_line": str(item).strip(),
                            "is_default": False,
                        }
                    )
            if cleaned and not any(i.get("is_default") for i in cleaned):
                cleaned[0]["is_default"] = True
            UserService._save_addresses(profile, cleaned)

        db.session.commit()
        return UserService.get_profile(user.id)

    @staticmethod
    def set_avatar_file(user_id: int, avatar_path: str) -> str:
        user = UserService._get_user(user_id)
        user.avatar = avatar_path
        db.session.commit()
        return avatar_path

    @staticmethod
    def get_addresses(user_id: int) -> list[dict]:
        user = UserService._get_user(user_id)
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        return UserService._load_addresses(profile.address if profile else None)

    @staticmethod
    def get_default_address(user_id: int) -> dict | None:
        addresses = UserService.get_addresses(user_id)
        return next((item for item in addresses if item.get("is_default")), None)

    @staticmethod
    def get_address_by_id(user_id: int, address_id: str) -> dict:
        address = next((item for item in UserService.get_addresses(user_id) if item["id"] == str(address_id)), None)
        if not address:
            raise NotFoundError("Không tìm thấy địa chỉ")
        return address

    @staticmethod
    def upsert_address(user_id: int, payload: dict) -> list[dict]:
        user = UserService._get_user(user_id)
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if profile is None:
            profile = UserProfile(user_id=user.id)
            db.session.add(profile)

        required_fields = ["full_name", "phone", "city", "district", "ward", "address_line"]
        for field in required_fields:
            if not str(payload.get(field) or "").strip():
                raise ValidationError("Vui lòng nhập đầy đủ thông tin địa chỉ")

        addresses = UserService._load_addresses(profile.address)
        address_id = str(payload.get("id") or payload.get("address_id") or "").strip()
        is_default = bool(payload.get("is_default", False))
        target = None
        if address_id:
            target = next((item for item in addresses if item["id"] == address_id), None)

        if target is None:
            target = {
                "id": address_id or uuid4().hex,
                "full_name": "",
                "phone": "",
                "city": "",
                "district": "",
                "ward": "",
                "address_line": "",
                "is_default": False,
            }
            addresses.append(target)


        target.update(
            {
                "full_name": str(payload.get("full_name") or "").strip(),
                "phone": str(payload.get("phone") or "").strip(),
                "city": str(payload.get("city") or "").strip(),
                "district": str(payload.get("district") or "").strip(),
                "ward": str(payload.get("ward") or "").strip(),
                "address_line": str(payload.get("address_line") or "").strip(),
                "is_default": is_default,
            }
        )
        if not addresses:
            target["is_default"] = True
        if target["is_default"]:
            for item in addresses:
                item["is_default"] = item["id"] == target["id"]
        elif not any(item.get("is_default") for item in addresses):
            addresses[0]["is_default"] = True

        UserService._save_addresses(profile, addresses)
        db.session.commit()
        return addresses
    @staticmethod
    def add_address(user_id: int, payload: dict) -> list[dict]:
        return UserService.upsert_address(user_id, payload)

    @staticmethod
    def delete_address(user_id: int, address_id: str) -> list[dict]:
        user = UserService._get_user(user_id)
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if profile is None:
            raise NotFoundError("Không tìm thấy địa chỉ")

        addresses = UserService._load_addresses(profile.address)
        kept = [item for item in addresses if item["id"] != address_id]
        if len(kept) == len(addresses):
            raise NotFoundError("Không tìm thấy địa chỉ")

        if kept and not any(i["is_default"] for i in kept):
            kept[0]["is_default"] = True

        UserService._save_addresses(profile, kept)
        db.session.commit()
        return kept

    @staticmethod
    def set_default_address(user_id: int, address_id: str) -> list[dict]:
        user = UserService._get_user(user_id)
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if profile is None:
            raise NotFoundError("Không tìm thấy địa chỉ")

        addresses = UserService._load_addresses(profile.address)
        found = False
        for item in addresses:
            item["is_default"] = item["id"] == address_id
            found = found or item["is_default"]

        if not found:
            raise NotFoundError("Không tìm thấy địa chỉ")

        UserService._save_addresses(profile, addresses)
        db.session.commit()
        return addresses

    # ==============================
    # PASSWORD
    # ==============================

    @staticmethod
    def change_password(user_id: int, current_password: str, new_password: str) -> None:
        if not current_password or not new_password:
            raise ValidationError("Thiếu thông tin đổi mật khẩu")

        if len(new_password) < 8:
            raise ValidationError("Mật khẩu mới phải tối thiểu 8 ký tự")

        user = UserService._get_user(user_id)

        if not check_password_hash(user.password_hash, current_password):
            raise ConflictError("Mật khẩu hiện tại không đúng")

        if check_password_hash(user.password_hash, new_password):
            raise ConflictError("Mật khẩu mới không được trùng mật khẩu cũ")
        user.password_hash = generate_password_hash(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()
    # ==============================
    # PURCHASE HISTORY
    # ==============================

    @staticmethod
    def purchase_history(user_id: int) -> list[dict]:
        UserService._get_user(user_id)

        orders = (
            Order.query.filter_by(user_id=user_id)
            .order_by(Order.created_at.desc())
            .all()
        )

        if not orders:
            return []

        order_ids = [order.id for order in orders]

        order_items = (
            OrderItem.query
            .filter(OrderItem.order_id.in_(order_ids))
            .all()
        )

        product_ids = {
            item.product_id
            for item in order_items
            if item.product_id is not None
        }

        products = (
            Product.query.filter(Product.id.in_(product_ids)).all()
            if product_ids
            else []
        )

        product_by_id = {product.id: product for product in products}

        items_by_order_id: dict[int, list[OrderItem]] = {
            order_id: [] for order_id in order_ids
        }

        for item in order_items:
            items_by_order_id.setdefault(
                item.order_id, []
            ).append(item)

        result = []

        for order in orders:
            items_data = []

            for item in items_by_order_id.get(order.id, []):
                product = product_by_id.get(item.product_id)
                quantity = item.quantity or 0
                price = item.price or Decimal("0")

                items_data.append(
                    {
                        "product_id": item.product_id,
                        "product_name": product.name
                        if product
                        else None,
                        "quantity": quantity,
                        "price": UserService._decimal_to_string(price),
                        "line_total": UserService._decimal_to_string(
                            price * quantity
                        ),
                    }
                )

            result.append(
                {
                    "order_id": order.id,
                    "status": order.status,
                    "payment_method": order.payment_method,
                    "total_price": UserService._decimal_to_string(
                        order.total_price
                    ),
                    "created_at": order.created_at.isoformat()
                    if order.created_at
                    else None,
                    "items": items_data,
                }
            )

        return result