from app.extensions.db import db
from .base import BaseModel
from datetime import datetime, timezone
from app.core.enums.product_status import ProductStatus


class ProductCategory(db.Model):
    __tablename__ = "product_categories"

    product_id = db.Column(db.BigInteger, db.ForeignKey("products.id"), primary_key=True)
    category_id = db.Column(db.BigInteger, db.ForeignKey("categories.id"), primary_key=True)

    is_primary = db.Column(db.Boolean, default=False)

    product = db.relationship("app.models.product.Product", back_populates="product_categories")
    category = db.relationship("app.models.product.Category", back_populates="product_categories")


class Product(BaseModel):
    __tablename__ = "products"

    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(255), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)

    # Không còn price và stock ở đây
    thumbnail = db.Column(db.String(500), nullable=True)

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    shop_id = db.Column(db.BigInteger, db.ForeignKey("shops.id"), nullable=True)

    status = db.Column(
        db.Enum(ProductStatus, name="product_status"),
        nullable=False,
        default=ProductStatus.ACTIVE,
        index=True,
    )

    product_categories = db.relationship(
        "app.models.product.ProductCategory",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    images = db.relationship(
        "app.models.product.ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    reviews = db.relationship(
        "app.models.review.Review",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    variants = db.relationship(
        "app.models.product.ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    shop = db.relationship("app.models.shop.Shop", backref="products")

class Category(BaseModel):
    __tablename__ = "categories"

    name = db.Column(db.String(100), nullable=False, unique=True)
    parent_id = db.Column(db.BigInteger, db.ForeignKey("categories.id"))

    parent = db.relationship(
        "app.models.product.Category",
        remote_side="Category.id",
        backref="children"
    )

    product_categories = db.relationship(
        "app.models.product.ProductCategory",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class ProductImage(BaseModel):
    __tablename__ = "product_images"

    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    image_url = db.Column(db.String(255), nullable=False)

    product = db.relationship(
        "app.models.product.Product",
        back_populates="images"
    )


# ==============================
# VARIANT SYSTEM
# ==============================

class ProductVariant(BaseModel):
    __tablename__ = "product_variants"

    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    sku = db.Column(db.String(100), unique=True, nullable=True)

    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    stock = db.Column(db.Integer, nullable=False, default=0)

    image_url = db.Column(db.String(500), nullable=True)
    # ================= SHIPPING =================

    weight = db.Column(db.Numeric(10,2), nullable=True)

    length = db.Column(db.Numeric(10,2), nullable=True)
    width = db.Column(db.Numeric(10,2), nullable=True)
    height = db.Column(db.Numeric(10,2), nullable=True)

    shipping_fast_fee = db.Column(db.Integer, default=0)
    shipping_same_day_fee = db.Column(db.Integer, default=0)
    shipping_express_fee = db.Column(db.Integer, default=0)
    shipping_pickup_fee = db.Column(db.Integer, default=0)
    shipping_bulky_fee = db.Column(db.Integer, default=0)
    product = db.relationship(
        "app.models.product.Product",
        back_populates="variants"
    )

    variant_attributes = db.relationship(
        "app.models.product.VariantAttribute",
        back_populates="variant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    def get_attr(self, name):

        for attr in self.variant_attributes:
            if attr.name == name:
                return attr.value

        return ""


class VariantAttribute(BaseModel):
    __tablename__ = "variant_attributes"

    variant_id = db.Column(
        db.BigInteger,
        db.ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False
    )

    name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=False)

    variant = db.relationship(
        "app.models.product.ProductVariant",
        back_populates="variant_attributes"
    )