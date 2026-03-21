from app.extensions import db
from app.common.exceptions import ValidationError
from app.models import Shop
from .dto import CreateShopDTO, ShippingSetupDTO
from slugify import slugify

class SellerService:
    @staticmethod
    def get_current_shop(user):
        if not user:
            return None
        return Shop.query.filter_by(owner_id=user.id).first()
    @staticmethod
    def _validate_step_1(dto: CreateShopDTO, current_shop_id: int | None = None):
        if not dto.name or len(dto.name.strip()) < 3:
            raise ValidationError("Tên shop tối thiểu 3 ký tự")
        if not dto.pickup_address or len(dto.pickup_address.strip()) < 10:
            raise ValidationError("Địa chỉ lấy hàng không hợp lệ")
        if not dto.email or "@" not in dto.email:
            raise ValidationError("Email liên hệ không hợp lệ")
        if not dto.phone or len(dto.phone.strip()) < 9:
            raise ValidationError("Số điện thoại liên hệ không hợp lệ")
        normalized_email = dto.email.strip().lower()
        normalized_phone = dto.phone.strip()

        email_query = Shop.query.filter(Shop.contact_email == normalized_email)
        phone_query = Shop.query.filter(Shop.contact_phone == normalized_phone)

        if current_shop_id is not None:
            email_query = email_query.filter(Shop.id != current_shop_id)
            phone_query = phone_query.filter(Shop.id != current_shop_id)

        if email_query.first() or phone_query.first():
            raise ValidationError("Email hoặc số điện thoại đã tồn tại")

    @staticmethod
    def register_shop(user, dto: CreateShopDTO):
        SellerService._validate_step_1(dto)

        existing_shop = Shop.query.filter_by(owner_id=user.id).first()
        if existing_shop:
            raise ValidationError("Bạn đã có shop, không thể tạo thêm")

        shop = Shop(
            owner_id=user.id,
            name=dto.name.strip(),
            pickup_address=dto.pickup_address.strip(),
            contact_email=dto.email.strip().lower(),
            contact_phone=dto.phone.strip(),
            onboarding_completed=False,
            onboarding_step=2,
            status="PENDING",
        )

        db.session.add(shop)
        user.is_seller = True
        user.role = "seller"
        db.session.commit()

        return shop

    @staticmethod
    def setup_shipping(shop: Shop, dto: ShippingSetupDTO):
        if not any([
            dto.fast,
            dto.same_day,
            dto.express,
            dto.self_delivery,
            dto.pickup_point,
            dto.bulky,
        ]):
            raise ValidationError("Vui lòng bật ít nhất một hình thức vận chuyển")

        shop.shipping_fast = dto.fast
        shop.shipping_same_day = dto.same_day
        shop.shipping_express = dto.express
        shop.shipping_self_delivery = dto.self_delivery
        shop.shipping_pickup_point = dto.pickup_point
        shop.shipping_bulky = dto.bulky

        shop.shipping_configured = True
        shop.onboarding_step = 2
        shop.onboarding_completed = True
        db.session.commit()

        return shop

    @staticmethod
    def update_shop(shop: Shop, dto: CreateShopDTO):
        SellerService._validate_step_1(dto, current_shop_id=shop.id)

        shop.name = dto.name.strip()
        shop.pickup_address = dto.pickup_address.strip()
        shop.contact_email = dto.email.strip().lower()
        shop.contact_phone = dto.phone.strip()
        if shop.onboarding_step < 2:
            shop.onboarding_step = 2

        db.session.commit()

        return shop
    
