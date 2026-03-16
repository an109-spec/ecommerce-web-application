from app.extensions.db import db
from .base import BaseModel


class Voucher(BaseModel):
    __tablename__ = "vouchers"

    shop_id = db.Column(
        db.BigInteger,
        db.ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False
    )

    name = db.Column(db.String(200), nullable=False)

    code = db.Column(db.String(50), nullable=False)

    discount_type = db.Column(db.String(20))  
    # percent / amount

    discount_value = db.Column(db.Integer)

    min_order_value = db.Column(db.Integer)

    usage_limit = db.Column(db.Integer)

    used_count = db.Column(db.Integer, default=0)

    start_time = db.Column(db.DateTime(timezone=True), nullable=False)

    end_time =db.Column(db.DateTime(timezone=True), nullable=False)

    is_active = db.Column(db.Boolean, default=True)

    shop = db.relationship("Shop", backref="vouchers")