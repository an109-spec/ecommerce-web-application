
from app.extensions.db import db
from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255))

    role = db.Column(
        db.Enum("user", "admin", "seller", name="user_roles"),
        default="user"
    )
    is_seller = db.Column(db.Boolean, default=False, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    locked_until = db.Column(db.DateTime, nullable=True)
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    profile = db.relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        primary_key=True
    )

    full_name = db.Column(db.String(120))
    address = db.Column(db.Text)
    gender = db.Column(db.String(20))
    birthday = db.Column(db.Date)

    # BẮT BUỘC PHẢI CÓ
    user = db.relationship(
        "User",
        back_populates="profile"
    )
