import uuid
from decimal import Decimal
from flask import session
from app.extensions.db import db
from app.models import Order, OrderItem, Product, OrderTracking, Review, User
from app.common.exceptions import (
    NotFoundError,
    ValidationError,
    ForbiddenError,
)
from app.core.enums.order_status import OrderStatus
from .workflow import apply_transition
from datetime import datetime, timezone

class OrderService:

    SESSION_KEY = "cart"

    @staticmethod
    def _generate_order_code():
        return uuid.uuid4().hex[:12].upper()

    @staticmethod
    def create_order_from_cart(user_id, payment_method):

        cart = session.get(OrderService.SESSION_KEY)

        if not cart or not cart.get("items"):
            raise ValidationError("Giỏ hàng trống")

        items = cart["items"]

        order = Order(
            user_id=user_id,
            total_price=Decimal("0"),
            subtotal=Decimal("0"),
            shipping_fee=Decimal("0"),
            status=OrderStatus.PENDING,
            payment_method=payment_method,
            order_code=OrderService._generate_order_code()
        )

        db.session.add(order)
        db.session.flush()

        total = Decimal("0")

        for item in items.values():
            product = Product.query.get(item["product_id"])

            if not product:
                raise NotFoundError("Sản phẩm không tồn tại")

            quantity = int(item["quantity"])

            if product.stock_quantity < quantity:
                raise ValidationError("Không đủ tồn kho")

            subtotal = product.price * quantity
            total += subtotal

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                price=product.price,
                quantity=quantity,
                subtotal=subtotal,
                product_name=product.name or "",
                product_thumbnail=product.thumbnail,
            )

            product.stock_quantity -= quantity
            db.session.add(order_item)
        order.subtotal = total
        order.total_price = total
        db.session.commit()

        session.pop(OrderService.SESSION_KEY, None)

        return order

    @staticmethod
    def cancel_order(order_id, user_id, by="BUYER", reason=None):
        order = (
            Order.query
            .filter(Order.id == order_id)
            .with_for_update()
            .first()
        )

        if not order:
            raise NotFoundError("Không tìm thấy đơn hàng")

        if by == "BUYER" and order.user_id != user_id:
            raise ForbiddenError("Không có quyền huỷ đơn")

        cancellable = [OrderStatus.PENDING, OrderStatus.CONFIRMED]
        if by == "SELLER":
            cancellable.append(OrderStatus.PREPARING)

        if order.status not in cancellable:
            raise ValidationError("Không thể huỷ đơn ở trạng thái này")

        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock_quantity += item.quantity

        order.cancelled_by = by
        order.cancel_reason = reason
        order.cancelled_at = datetime.now(timezone.utc)
        db.session.commit()
        return order

    @staticmethod
    def get_user_orders(user_id, status=None):

        query = (
            Order.query
            .filter_by(user_id=user_id)
            .order_by(Order.created_at.desc())
        )
        if status and status != "ALL":
            query = query.filter(Order.status == OrderStatus.from_input(status))
        orders = query.all()
        return orders

    @staticmethod
    def get_order_detail(order_id, user_id):

        order = db.session.get(Order, order_id)

        if not order:
            raise NotFoundError("Không tìm thấy đơn hàng")

        if order.user_id != user_id:
            raise ForbiddenError("Không có quyền xem đơn này")

        return order


    @staticmethod
    def get_order_detail_for_seller(order_id, shop_id):
        order = (
            Order.query
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Order.id == order_id, Product.shop_id == shop_id)
            .first()
        )
        if not order:
            raise NotFoundError("Không tìm thấy đơn hàng")
        return order


    @staticmethod
    def update_status(order_id, new_status):
        order = db.session.get(Order, order_id)

        if not order:
            raise NotFoundError("Không tìm thấy đơn hàng")

        apply_transition(order, new_status)
        db.session.commit()
    @staticmethod
    def get_all_orders():
        return (
            Order.query
            .order_by(Order.created_at.desc())
            .all()
        )

    @staticmethod
    def get_order_detail_admin(order_id):
        order = db.session.get(Order, order_id)

        if not order:
            raise NotFoundError("Không tìm thấy đơn hàng")

        return order

    @staticmethod
    def track_by_order_code(order_code):
        order = (
            Order.query
            .filter_by(order_code=order_code)
            .first()
        )

        if not order:
            raise NotFoundError("Không tìm thấy đơn hàng")

        return order

    @staticmethod
    def build_timeline(order):
        if order.status == OrderStatus.CANCELLED:
            return [{
                "label": "Đặt hàng",
                "active": True,
                "time": order.created_at.strftime("%d/%m %H:%M") if order.created_at else ""
            }, {
                "label": f"✖ Đơn hàng đã bị hủy bởi {order.cancelled_by or 'SYSTEM'}",
                "active": True,
                "time": order.cancelled_at.strftime("%d/%m %H:%M") if order.cancelled_at else ""
            }]

        steps = [
            ("Đặt hàng", order.created_at),
            ("Người bán xác nhận", order.confirmed_at),
            ("Đang chuẩn bị", order.preparing_at),
            ("Đang giao", order.shipping_at),
            ("Đã giao", order.delivered_at),
        ]

        timeline = []
        for idx, (label, ts) in enumerate(steps):
            is_active = ts is not None or (
                idx == 0 and order.status in {
                    OrderStatus.PENDING,
                    OrderStatus.CONFIRMED,
                    OrderStatus.PREPARING,
                    OrderStatus.SHIPPING,
                    OrderStatus.DELIVERED,
                }
            )
            timeline.append({
                "label": label,
                "active": is_active,
                "time": ts.strftime("%d/%m %H:%M") if ts else ""
            })

        return timeline

    @staticmethod
    def get_customer_info(order):
        user = db.session.get(User, order.user_id)
        profile = user.profile if user else None
        return {
            "name": (profile.full_name if profile and profile.full_name else (user.username if user else "")),
            "phone": user.phone if user else "",
            "address": profile.address if profile else "",
        }
    @staticmethod
    def has_review_by_user(order, user_id):
        item_ids = [item.id for item in order.items]
        if not item_ids:
            return False
        return (
            Review.query
            .filter(Review.user_id == user_id, Review.order_item_id.in_(item_ids))
            .first()
            is not None
        )