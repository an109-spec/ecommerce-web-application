from app.extensions.db import db
from .base import BaseModel
from app.core.enums.order_status import OrderStatus, PaymentMethod
from datetime import datetime, timezone

class Order(BaseModel):
    __tablename__ = "orders"

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    total_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    status = db.Column(
        db.Enum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True
    )

    payment_method = db.Column(
        db.Enum(PaymentMethod, name="payment_method_enum"),
        nullable=False
    )

    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    shipping_fee = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    cancelled_by = db.Column(db.String(20), nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)
    cancelled_at = db.Column(db.DateTime(timezone=True), nullable=True)
    confirmed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    preparing_at = db.Column(db.DateTime(timezone=True), nullable=True)
    shipping_at = db.Column(db.DateTime(timezone=True), nullable=True)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)

    items = db.relationship(
        "OrderItem",
        backref="order",
        cascade="all, delete-orphan",
        lazy=True
    )


class OrderItem(BaseModel):
    __tablename__ = "order_items"

    order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey("products.id"),
        nullable=False
    )

    price = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    subtotal = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    product_name = db.Column(db.String(255), nullable=False, default="")
    product_thumbnail = db.Column(db.String(500), nullable=True)

class OrderTracking(BaseModel):
    __tablename__ = "order_tracking"

    order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )
    status = db.Column(
    db.Enum(OrderStatus, name="order_status"),
    nullable=False
)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    order_code = db.Column(
    db.String(30),
    unique=True,
    nullable=False,
    index=True
)