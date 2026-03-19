from sqlalchemy import func
from app.extensions import db
from app.models import ProductImage, Shop, Order, OrderItem, ChatRoom, Message
from app.core.enums.order_status import OrderStatus
from app.core.enums.product_status import ProductStatus
from app.models.product import ProductVariant, VariantAttribute, Product
import os
import uuid
from werkzeug.utils import secure_filename
from app.models.promotion import Promotion
from sqlalchemy import cast, String


class SellerRepository:

    @staticmethod
    def get_shop_by_owner_id(owner_id: int):
        return Shop.query.filter_by(owner_id=owner_id).first()

    @staticmethod
    def get_shop_by_id(shop_id: int):
        return db.session.get(Shop, shop_id)

    @staticmethod
    def create_product(product: Product):
        db.session.add(product)
        db.session.flush()
        return product

    @staticmethod
    def create_product_images(product_id: int, image_urls: list[str]):
        images = [ProductImage(product_id=product_id, image_url=url) for url in image_urls]
        db.session.add_all(images)

    @staticmethod
    def list_products(shop_id: int):
        return (
            Product.query
            .filter(
                Product.shop_id == shop_id,
                Product.status != ProductStatus.DELETED,
            )
            .order_by(Product.created_at.desc())
            .all()
        )

    @staticmethod
    def get_product(shop_id, product_id):
        return Product.query.filter_by(
            id=product_id,
            shop_id=shop_id
        ).first()

    @staticmethod
    def get_orders_by_shop(shop_id: int, status: OrderStatus | None = None):

        query = (
            Order.query
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Product.shop_id == shop_id)
            .distinct()
            .order_by(Order.created_at.desc())
        )

        if status:
            print("DEBUG STATUS:", status, type(status))
            print("DEBUG VALUE:", getattr(status, "value", None))
            #query = query.filter(cast(Order.status, String) == status.value)
            if status:
                query = query.filter(Order.status == status)

        return query.all()

    @staticmethod
    def get_order_by_shop(order_id: int, shop_id: int):
        return (
            Order.query
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(
                Order.id == order_id,
                Product.shop_id == shop_id
            )
            .first()
        )

    @staticmethod
    def list_chat_rooms_for_seller(seller_id: int):
        return (
            ChatRoom.query
            .filter_by(seller_id=seller_id)
            .order_by(ChatRoom.created_at.desc())
            .all()
        )

    @staticmethod
    def list_messages(room_id: int, limit: int = 50):
        return (
            Message.query
            .filter_by(room_id=room_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def commit():
        db.session.commit()

    @staticmethod
    def get_shop_revenue(shop_id: int):

        revenue = (
            db.session.query(func.sum(OrderItem.price * OrderItem.quantity))
            .join(Product, Product.id == OrderItem.product_id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                Product.shop_id == shop_id,
                Order.status == OrderStatus.DELIVERED.value
            )
            .scalar()
        )

        return revenue or 0
    @staticmethod
    def create_product_variants(product_id, variants):

        for data in variants:

            image_file = data.get("image")
            
            if hasattr(image_file, "filename") and image_file.filename:
                filename = str(uuid.uuid4()) + "_" + secure_filename(image_file.filename)

                save_path = os.path.join(
                    "app/static/uploads/products",
                    filename
                )

                image_file.save(save_path)

                image_url = "/static/uploads/products/" + filename
            elif isinstance(image_file, str) and image_file.strip():
                image_url = image_file
            else:
                image_url = None
            variant = ProductVariant(
                product_id=product_id,
                price=data["price"],
                stock=data["stock"],
                image_url=image_url,

                weight=data.get("weight"),
                length=data.get("length"),
                width=data.get("width"),
                height=data.get("height"),

                shipping_fast_fee=data.get("shipping_fast_fee", 0),
                shipping_same_day_fee=data.get("shipping_same_day_fee", 0),
                shipping_express_fee=data.get("shipping_express_fee", 0),
                shipping_pickup_fee=data.get("shipping_pickup_fee", 0),
                shipping_bulky_fee=data.get("shipping_bulky_fee", 0),
            )

            db.session.add(variant)
            db.session.flush()

            for name, value in data["attributes"].items():

                attr = VariantAttribute(
                    variant_id=variant.id,
                    name=name,
                    value=value
                )

                db.session.add(attr)

    @staticmethod
    def delete_variants(product_id):

        variants = ProductVariant.query.filter_by(
            product_id=product_id
        ).all()

        variant_ids = [v.id for v in variants]

        # 🔥 XÓA PROMOTION TRƯỚC
        if variant_ids:
            Promotion.query.filter(
                Promotion.variant_id.in_(variant_ids)
            ).delete(synchronize_session=False)

        # 🔥 SAU ĐÓ mới xoá variant
        for v in variants:
            db.session.delete(v)

