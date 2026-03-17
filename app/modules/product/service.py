from app.common.exceptions import ConflictError, NotFoundError
from app.extensions.db import db

from .dto import ProductCreateDTO, ProductResponseDTO, ProductUpdateDTO, ReviewCreateDTO
from .filters import filter_by_category, filter_by_price, sort_products
from app.models.product import Product, ProductImage
from app.core.enums.product_status import ProductStatus
from datetime import datetime, timezone
from app.models.flash_sale import FlashSale
from app.models.review import Review
from app.models.shop import Shop
from .search import full_text_query


class ProductService:
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
            category_id=data.category_id,
            thumbnail=data.thumbnail,
        )
        db.session.add(product)
        db.session.flush()

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
        if data.category_id_provided:
            product.category_id = data.category_id
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

        size_options = sorted(
            {
                attr.value
                for variant in variants
                for attr in variant.variant_attributes
                if (attr.name or "").strip().lower() == "size"
            }
        )
        color_options = sorted(
            {
                attr.value
                for variant in variants
                for attr in variant.variant_attributes
                if (attr.name or "").strip().lower() == "color"
            }
        )

        primary_category = product.product_categories[0].category.name if product.product_categories else None
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
            "stock": total_stock,
            "category": primary_category,
            "shop": {
                "id": shop.id if shop else None,
                "name": shop.name if shop else "OneShop",
                "logo": ProductService._normalize_asset_url(shop.logo if shop else None),
                "rating": float(shop.rating) if shop and shop.rating is not None else 0.0,
                "total_products": shop_total_products,
                "followers": 0,
                "url": f"/shop/search?shop_id={shop.id}" if shop else "/shop",
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

        review = Review(
            product_id=product_id,
            user_id=user_id,
            rating=data.rating,
            comment=data.comment,
        )
        db.session.add(review)
        db.session.commit()

        return {
            "id": review.id,
            "product_id": review.product_id,
            "user_id": review.user_id,
            "rating": review.rating,
            "comment": review.comment,
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