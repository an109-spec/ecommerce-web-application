from app.extensions.db import db
from .base import BaseModel
from datetime import datetime, timezone


class Shop(BaseModel):
    __tablename__ = "shops"

    owner_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=False
    )

    name = db.Column(db.String(150), nullable=False)
    pickup_address = db.Column(db.Text)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    legal_id = db.Column(db.String(50))
    legal_name = db.Column(db.String(150))
    tax_code = db.Column(db.String(50))
    tax_address = db.Column(db.Text)
    onboarding_step = db.Column(db.Integer, default=1, nullable=False)
    onboarding_completed = db.Column(db.Boolean, default=False, nullable=False)
    logo = db.Column(db.String(255))
    banner = db.Column(db.String(255))
    description = db.Column(db.Text)
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    status = db.Column(
        db.Enum("PENDING", "ACTIVE", "BANNED", name="shop_status"),
        default="PENDING",
        nullable=False,
        index=True,
    )

    # =====================
    # SHIPPING SETTINGS
    # =====================
    shipping_fast = db.Column(db.Boolean, default=True)
    shipping_same_day = db.Column(db.Boolean, default=True)
    shipping_express = db.Column(db.Boolean, default=True)
    shipping_self_delivery = db.Column(db.Boolean, default=False)
    shipping_pickup_point = db.Column(db.Boolean, default=False)
    shipping_bulky = db.Column(db.Boolean, default=False)

    shipping_configured = db.Column(db.Boolean, default=False)
    shipping_fee = db.Column(db.Numeric(12, 2), default=0)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    owner = db.relationship(
    "User",
    backref=db.backref("shop", uselist=False)
)