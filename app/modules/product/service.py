from app.common.exceptions import ConflictError, NotFoundError, ValidationError, ForbiddenError
from app.extensions.db import db

from .dto import ProductCreateDTO, ProductResponseDTO, ProductUpdateDTO, ReviewCreateDTO
from .filters import filter_by_category, filter_by_price, sort_products
from app.models.product import Category, Product, ProductImage, ProductCategory
from app.core.enums.product_status import ProductStatus
from datetime import datetime, timezone
from app.models.flash_sale import FlashSale
from app.models.review import Review
from app.models.shop import Shop
from app.models.order import Order, OrderItem
from app.core.enums.order_status import OrderStatus
from .search import full_text_query
from sqlalchemy import inspect, text
from app.models.shop_follow import ShopFollow

class ProductService:
    @staticmethod
    def _get_category_names(product: Product) -> list[str]:
        category_names = [
            pc.category.name
            for pc in (product.product_categories or [])
            if pc.category and pc.category.name
        ]
        if category_names:
            return category_names

        product_columns = {
            column["name"]
            for column in inspect(db.engine).get_columns("products")
        }
        if "category_id" not in product_columns:
            return []

        legacy_category_id = db.session.execute(
            text("SELECT category_id FROM products WHERE id = :product_id"),
            {"product_id": product.id},
        ).scalar()
        if not legacy_category_id:
            return []

        legacy_category = db.session.get(Category, legacy_category_id)
        return [legacy_category.name] if legacy_category and legacy_category.name else []

    @staticmethod
    def _normalize_asset_url(src: str | None, fallback: str = "/static/images/no-image.png") -> str:
        if not src:
            return fallback
        if src.startswith(("http://", "https://", "/")):
            return src
        if src.startswith("static/"):
            return f"/{src}"
        return f"/static/{src}"

    @staticmethod
    def list_products(*, keyword=None, min_price=None, max_price=None, category=None, sort=None, page=1, per_page=10):
        query = Product.query.filter(Product.status == ProductStatus.ACTIVE)
        query = full_text_query(query, keyword)
        query = filter_by_price(query, min_price, max_price)
        query = filter_by_category(query, category)
        query = sort_products(query, sort)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "items": [ProductResponseDTO.from_model(item).to_dict() for item in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create_product(data: ProductCreateDTO):
        exists = Product.query.filter_by(slug=data.slug).first()
        if exists:
            raise ConflictError("slug đã tồn tại")

        product = Product(
            name=data.name,
            slug=data.slug,
            description=data.description,
            price=data.price,
            stock_quantity=data.stock_quantity,
            thumbnail=data.thumbnail,
        )
        db.session.add(product)
        db.session.flush()
        if data.category_ids:
            for i, cat_id in enumerate(data.category_ids):
                db.session.add(ProductCategory(
                    product_id=product.id,
                    category_id=cat_id,
                    is_primary=(i == 0)
                ))

        if data.thumbnail:
            db.session.add(ProductImage(product_id=product.id, image_url=data.thumbnail))

        db.session.commit()
        return ProductResponseDTO.from_model(product).to_dict()

    @staticmethod
    def update_product(product_id: int, data: ProductUpdateDTO):
        product = Product.query.filter(Product.id == product_id, Product.status != ProductStatus.DELETED).first()
        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")

        if data.slug is not None and data.slug != product.slug:
            exists = Product.query.filter(Product.slug == data.slug, Product.id != product_id).first()
            if exists:
                raise ConflictError("slug đã tồn tại")
            product.slug = data.slug

        if data.name is not None:
            product.name = data.name
        if data.description is not None:
            product.description = data.description
        if data.price is not None:
            product.price = data.price
        if data.stock_quantity is not None:
            product.stock_quantity = data.stock_quantity
        if data.category_ids_provided:
            product.product_categories.clear()
            for i, cat_id in enumerate(data.category_ids or []):
                db.session.add(ProductCategory(
                    product_id=product.id,
                    category_id=cat_id,
                    is_primary=(i == 0)
                ))
        if data.thumbnail is not None:
            product.thumbnail = data.thumbnail

        db.session.commit()
        return ProductResponseDTO.from_model(product).to_dict()

    @staticmethod
    def delete_product(product_id: int):
        product = Product.query.filter(Product.id == product_id, Product.status == ProductStatus.ACTIVE).first()
        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")

        product.status = ProductStatus.DELETED
        db.session.commit()

    @staticmethod
    def get_product_detail(product_id: int):
        product = Product.query.filter(Product.id == product_id, Product.status == ProductStatus.ACTIVE).first()
        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")

        variants = product.variants or []
        prices = [variant.price for variant in variants]
        stocks = [variant.stock for variant in variants]

        original_price = min(prices) if prices else 0
        total_stock = int(sum(stocks)) if stocks else 0

        review_count = len(product.reviews)
        avg_rating = float(sum(review.rating for review in product.reviews) / review_count) if review_count else 0.0

        now = datetime.now(timezone.utc)
        active_sale = None
        for variant in variants:
            sale = (
                FlashSale.query
                .filter(
                    FlashSale.variant_id == variant.id,
                    FlashSale.is_active.is_(True),
                    FlashSale.start_time <= now,
                    FlashSale.end_time >= now,
                )
                .order_by(FlashSale.end_time.asc())
                .first()
            )
            if sale:
                active_sale = sale
                break

        flash_price = None
        discount_percent = 0
        flash_ends_at = None
        if active_sale and active_sale.variant:
            discount_percent = int(active_sale.discount_percent or 0)
            flash_price = float(active_sale.variant.price * (100 - discount_percent) / 100)
            flash_ends_at = active_sale.end_time.isoformat()
        def _normalized_key(value: str | None) -> str:
            return (value or "").strip().lower()

        size_keys = {"size", "kích thước", "kich thuoc"}
        color_keys = {"color", "màu", "mau"}

        size_options = sorted(
            {
                attr.value
                for variant in variants
                for attr in variant.variant_attributes
                if _normalized_key(attr.name) in size_keys and (attr.value or "").strip()
            }
        )
        color_options = sorted(
            {
                attr.value
                for variant in variants
                for attr in variant.variant_attributes
                 if _normalized_key(attr.name) in color_keys and (attr.value or "").strip()
            }
        )

        category_names = ProductService._get_category_names(product)
        primary_category = category_names[0] if category_names else None
        shop = Shop.query.get(product.shop_id) if product.shop_id else None
        shop_total_products = Product.query.filter(Product.shop_id == product.shop_id, Product.status == ProductStatus.ACTIVE).count() if product.shop_id else 0

        payload = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "thumbnail": ProductService._normalize_asset_url(product.thumbnail),

            "images": [ProductService._normalize_asset_url(img.image_url) for img in product.images]
            or ([ProductService._normalize_asset_url(product.thumbnail)] if product.thumbnail else []),

            "rating": round(avg_rating, 1),
            "reviews_count": review_count,

            "original_price": float(original_price),
            "flash_price": flash_price,
            "discount_percent": discount_percent,
            "flash_sale_ends_at": flash_ends_at,

            "size_options": size_options,
            "color_options": color_options,
            "variants": [
                    {
                        "id": v.id,
                        "price": float(v.price),
                        "stock": v.stock,
                        "image": ProductService._normalize_asset_url(v.image_url) if v.image_url else None,

                        "size": next(
                        (a.value for a in (v.variant_attributes or [])
                        if (a.name or "").strip().lower() in ["size", "kích thước", "kich thuoc"]),
                        None
                    ),

                        "color": next(
                            (a.value for a in v.variant_attributes
                            if (a.name or "").strip().lower() in ["color", "màu", "mau"]),
                            None
                        ),
                    }
                    for v in variants
                ],
            "stock": total_stock,
            "categories": category_names,
            "shop": {
                "id": shop.id if shop else None,
                "name": shop.name if shop else "OneShop",
                "logo": ProductService._normalize_asset_url(shop.logo if shop else None),
                "rating": float(shop.rating) if shop and shop.rating is not None else 0.0,
                "total_products": shop_total_products,
                "followers": ShopFollow.query.filter_by(shop_id=shop.id).count() if shop else 0,
                "url": f"/shops/{shop.id}" if shop else "/shop",
            },
        }
        return payload

    @staticmethod
    def get_related_products(product_id: int):
        product = Product.query.filter(Product.id == product_id, Product.status == ProductStatus.ACTIVE).first()
        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")

        related_query = Product.query.filter(Product.id != product_id, Product.status == ProductStatus.ACTIVE)

        related = related_query.order_by(Product.created_at.desc()).limit(8).all()
        payload = []
        for item in related:
            prices = [variant.price for variant in (item.variants or [])]
            payload.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "price": float(min(prices)) if prices else 0.0,
                    "thumbnail": ProductService._normalize_asset_url(item.thumbnail),
                    "image": ProductService._normalize_asset_url(item.thumbnail),
                }
            )
        return payload

    @staticmethod
    def add_review(product_id: int, user_id: int, data: ReviewCreateDTO):
        product = Product.query.filter(Product.id == product_id, Product.status == ProductStatus.ACTIVE).first()
        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")
        if data.user_id != user_id:
            raise ForbiddenError("Không có quyền đánh giá")
        if not data.order_id or not data.order_item_id:
            raise ValidationError("Thiếu thông tin đơn hàng để đánh giá")

        order = Order.query.filter_by(id=data.order_id, user_id=user_id).first()
        if not order:
            raise NotFoundError("Không tìm thấy đơn hàng")
        if order.status != OrderStatus.DELIVERED:
            raise ValidationError("Chỉ có thể đánh giá khi đơn đã giao")

        order_item = OrderItem.query.filter_by(id=data.order_item_id, order_id=order.id, product_id=product_id).first()
        if not order_item:
            raise ValidationError("Sản phẩm không thuộc đơn hàng")

        existed = Review.query.filter_by(user_id=user_id, order_item_id=order_item.id).first()
        if existed:
            raise ValidationError("Bạn đã đánh giá sản phẩm này trong đơn hàng")

        shop = Shop.query.get(product.shop_id) if product.shop_id else None
        old_count = 0
        old_avg = 0.0
        if shop:
            old_count = len(Review.query.join(Product, Product.id == Review.product_id).filter(Product.shop_id == shop.id).all())
            old_avg = float(shop.rating or 0)

        review = Review(
            product_id=product_id,
            user_id=user_id,
            rating=data.rating,
            comment=data.comment,
            order_id=order.id,
            order_item_id=order_item.id,
            size=data.size,
            color=data.color,
            media_url=data.media_url,
        )
        db.session.add(review)

        # Cập nhật rating shop theo công thức cộng dồn
        if shop:
            new_count = old_count + 1
            shop.rating = round(((old_avg * old_count) + data.rating) / new_count, 2)

        db.session.commit()

        return {
            "id": review.id,
            "product_id": review.product_id,
            "user_id": review.user_id,
            "rating": review.rating,
            "comment": review.comment,
            "size": review.size,
            "color": review.color,
            "media_url": review.media_url,
            "created_at": review.created_at.isoformat(),
        }

    @staticmethod
    def get_product_reviews(product_id: int):
        product = Product.query.filter(Product.id == product_id, Product.status == ProductStatus.ACTIVE).first()
        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")

        reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
        return [
            {
                "id": review.id,
                "product_id": review.product_id,
                "user_id": review.user_id,
                "rating": review.rating,
                "comment": review.comment,
                "size": review.size,
                "color": review.color,
                "media_url": review.media_url,
                "created_at": review.created_at.isoformat(),
            }
            for review in reviews
        ]
    @staticmethod
    def get_products_by_shop(shop_id: int):
        products = Product.query.filter(
            Product.shop_id == shop_id,
            Product.status == ProductStatus.ACTIVE
        ).order_by(Product.created_at.desc()).all()

        return products