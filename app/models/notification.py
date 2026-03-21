from app.extensions.db import db
from .base import BaseModel


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))