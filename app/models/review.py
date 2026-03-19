from app.extensions.db import db
from .base import BaseModel


class Review(BaseModel):
    __tablename__ = "reviews"

    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    product_id = db.Column(db.BigInteger, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    order_item_id = db.Column(db.BigInteger, db.ForeignKey("order_items.id", ondelete="SET NULL"), nullable=True, index=True)

    rating = db.Column(db.SmallInteger, nullable=False)
    comment = db.Column(db.Text)
    size = db.Column(db.String(100), nullable=True)
    color = db.Column(db.String(100), nullable=True)
    media_url = db.Column(db.String(500), nullable=True)
    product = db.relationship("app.models.product.Product", back_populates="reviews")
    __table_args__ = (
        db.UniqueConstraint("user_id", "order_item_id", name="uq_user_order_item_review"),
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
    )



