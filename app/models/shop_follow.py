from app.extensions.db import db
from .base import BaseModel


class ShopFollow(BaseModel):
    __tablename__ = "shop_follows"

    shop_id = db.Column(
        db.BigInteger,
        db.ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        db.UniqueConstraint("shop_id", "user_id", name="uq_shop_follow_shop_user"),
    )