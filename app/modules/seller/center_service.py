from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from app.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.enums.order_status import OrderStatus

from .repository import SellerRepository


@dataclass
class ShopUpdateDTO:
    name: str
    logo: str | None
    description: str | None
    address: str


@dataclass
class PromotionCreateDTO:
    product_id: int
    discount_percent: int
    start_time: datetime
    end_time: datetime


class SellerCenterService:
    @staticmethod
    def get_dashboard(shop_id: int):
        orders = SellerRepository.get_orders_by_shop(shop_id)
        products = SellerRepository.list_products(shop_id)

        pending = sum(1 for o in orders if o.status == OrderStatus.PENDING)
        preparing = sum(1 for o in orders if o.status == OrderStatus.PREPARING)
        shipping = sum(1 for o in orders if o.status == OrderStatus.SHIPPING)
        cancelled = sum(1 for o in orders if o.status == OrderStatus.CANCELLED)

        today = datetime.now(timezone.utc).date()
        today_revenue = sum(Decimal(o.total_price) for o in orders if o.created_at.date() == today and o.status != OrderStatus.CANCELLED)

        return {
            "todo": {
                "pending": pending,
                "preparing": preparing,
                "shipping": shipping,
                "cancelled": cancelled,
            },
            "today_revenue": float(today_revenue),
            "total_orders": len(orders),
            "total_products": len(products),
            "recent_orders": orders[:5],
        }

    @staticmethod
    def list_orders(shop_id: int, status: str | None):
        order_status = None
        if status and status.upper() != "ALL":
            try:
                order_status = OrderStatus.from_input(status)
            except ValueError as e:
                raise ValidationError("Trạng thái đơn hàng không hợp lệ") from e
        return SellerRepository.get_orders_by_shop(shop_id, order_status)

    @staticmethod
    def update_order_status(shop_id: int, order_id: int, status: str):
        try:
            new_status = OrderStatus.from_input(status)
        except ValueError as e:
            raise ValidationError("Trạng thái đơn hàng không hợp lệ") from e

        order = SellerRepository.get_order_by_shop(order_id, shop_id)
        if not order:
            raise NotFoundError("Không tìm thấy đơn hàng")

        order.status = new_status
        SellerRepository.commit()
        return order

    @staticmethod
    def get_chat_overview(seller_id: int):
        rooms = SellerRepository.list_chat_rooms_for_seller(seller_id)
        return rooms

    @staticmethod
    def get_revenue_summary(shop_id: int):
        revenue = Decimal(SellerRepository.get_shop_revenue(shop_id))

        delivered_orders = SellerRepository.get_orders_by_shop(
            shop_id,
            OrderStatus.DELIVERED
        )

        platform_fee = revenue * Decimal("0.05")
        shipping = revenue * Decimal("0.02")
        profit = revenue - platform_fee - shipping

        return {
            "orders": len(delivered_orders),
            "revenue": float(revenue),
            "platform_fee": float(platform_fee),
            "shipping": float(shipping),
            "profit": float(profit),
            "formula": "profit = revenue - platform_fee - shipping",
        }

    @staticmethod
    def update_shop(shop_id: int, dto: ShopUpdateDTO):
        shop = SellerRepository.get_shop_by_id(shop_id)
        if not shop:
            raise ForbiddenError("Không tìm thấy shop")

        if not dto.name or len(dto.name.strip()) < 3:
            raise ValidationError("Tên shop tối thiểu 3 ký tự")
        if not dto.address or len(dto.address.strip()) < 10:
            raise ValidationError("Địa chỉ không hợp lệ")

        shop.name = dto.name.strip()
        shop.logo = dto.logo
        shop.description = dto.description
        shop.pickup_address = dto.address.strip()
        SellerRepository.commit()
        return shop

    @staticmethod
    def create_promotion(shop_id: int, dto: PromotionCreateDTO):
        product = SellerRepository.get_product(dto.product_id)
        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")
        if product.shop_id != shop_id:
            raise ForbiddenError("Không thể tạo khuyến mãi cho sản phẩm shop khác")
        if dto.discount_percent <= 0 or dto.discount_percent >= 100:
            raise ValidationError("discount_percent phải trong khoảng 1-99")
        if dto.end_time <= dto.start_time:
            raise ValidationError("Thời gian khuyến mãi không hợp lệ")

        discount_rate = Decimal(dto.discount_percent) / Decimal(100)
        discount_price = Decimal(product.price) * (Decimal(1) - discount_rate)

        promotion = SellerRepository.create_flash_sale(
            product_id=product.id,
            discount_price=discount_price,
            start_time=dto.start_time,
            end_time=dto.end_time,
        )
        SellerRepository.commit()
        return promotion