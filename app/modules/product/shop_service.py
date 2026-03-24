from sqlalchemy import func

from app.common.exceptions import NotFoundError, UnauthorizedError, ValidationError
from app.core.enums.product_status import ProductStatus
from app.extensions.db import db
from app.models import OrderItem, Product, ProductVariant, Review, Shop, ShopFollow


class PublicShopService:
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
    def _product_base_query(shop_id: int):
        shop = Shop.query.get(shop_id)
        if not shop:
            raise NotFoundError("Không tìm thấy shop")

        sold_subquery = (
            db.session.query(
                OrderItem.product_id.label("product_id"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("sold_count"),
            )
            .group_by(OrderItem.product_id)
            .subquery()
        )

        rating_subquery = (
            db.session.query(
                Review.product_id.label("product_id"),
                func.coalesce(func.avg(Review.rating), 0).label("avg_rating"),
            )
            .group_by(Review.product_id)
            .subquery()
        )

        price_subquery = (
            db.session.query(
                ProductVariant.product_id.label("product_id"),
                func.coalesce(func.min(ProductVariant.price), 0).label("min_price"),
            )
            .group_by(ProductVariant.product_id)
            .subquery()
        )

        query = (
            db.session.query(
                Product,
                func.coalesce(sold_subquery.c.sold_count, 0).label("sold_count"),
                func.coalesce(rating_subquery.c.avg_rating, 0).label("avg_rating"),
                func.coalesce(price_subquery.c.min_price, 0).label("min_price"),
            )
            .filter(
                Product.shop_id == shop_id,
                Product.status == ProductStatus.ACTIVE,
            )
            .outerjoin(sold_subquery, sold_subquery.c.product_id == Product.id)
            .outerjoin(rating_subquery, rating_subquery.c.product_id == Product.id)
            .outerjoin(price_subquery, price_subquery.c.product_id == Product.id)
        )
        return shop, query

    @staticmethod
    def _serialize_product(product: Product, sold_count: int, avg_rating: float, min_price: float) -> dict:
        return {
            "id": product.id,
            "name": product.name,
            "thumbnail": PublicShopService._normalize_asset_url(product.thumbnail),
            "rating": round(float(avg_rating or 0), 1),
            "price": float(min_price or 0),
            "sold": int(sold_count or 0),
            "product_url": f"/shop/{product.id}",
        }

    @staticmethod
    def get_shop_profile(shop_id: int, current_user_id: int | None = None) -> dict:
        shop = Shop.query.get(shop_id)
        if not shop:
            raise NotFoundError("Không tìm thấy shop")

        total_products = Product.query.filter(
            Product.shop_id == shop_id,
            Product.status == ProductStatus.ACTIVE,
        ).count()

        followers_count = ShopFollow.query.filter_by(shop_id=shop_id).count()

        avg_rating = (
            db.session.query(func.coalesce(func.avg(Review.rating), 0))
            .select_from(Product)
            .outerjoin(Review, Review.product_id == Product.id)
            .filter(
                Product.shop_id == shop_id,
                Product.status == ProductStatus.ACTIVE,
            )
            .scalar()
        )

        is_following = False
        if current_user_id:
            is_following = (
                ShopFollow.query.filter_by(shop_id=shop_id, user_id=current_user_id).first()
                is not None
            )

        return {
            "id": shop.id,
            "owner_id": shop.owner_id,
            "name": shop.name,
            "logo": PublicShopService._normalize_asset_url(shop.logo),
            "rating": round(float(avg_rating or shop.rating or 0), 1),
            "followers_count": followers_count,
            "total_products": total_products,
            "description": shop.description or "",
            "is_following": is_following,
            "can_follow": current_user_id is None or current_user_id != shop.owner_id,
        }

    @staticmethod
    def list_products(
        shop_id: int,
        *,
        filter_by: str = "all",
        sort_by: str = "popular",
        page: int = 1,
        limit: int = 9,
    ) -> dict:
        filter_by = (filter_by or "all").strip().lower()
        sort_by = (sort_by or "").strip().lower()

        if filter_by not in {"all", "popular", "newest"}:
            raise ValidationError("Bộ lọc shop không hợp lệ")
        if sort_by and sort_by not in {"popular", "newest", "price_asc", "price_desc"}:
            raise ValidationError("Sắp xếp shop không hợp lệ")

        _, query = PublicShopService._product_base_query(shop_id)

        applied_sort = sort_by or ("popular" if filter_by == "popular" else "newest")
        if applied_sort == "popular":
            query = query.order_by(db.desc("sold_count"), Product.created_at.desc(), Product.id.desc())
        elif applied_sort == "newest":
            query = query.order_by(Product.created_at.desc(), Product.id.desc())
        elif applied_sort == "price_asc":
            query = query.order_by(db.asc("min_price"), Product.created_at.desc())
        elif applied_sort == "price_desc":
            query = query.order_by(db.desc("min_price"), Product.created_at.desc())

        pagination = query.paginate(page=page, per_page=limit, error_out=False)
        items = [
            PublicShopService._serialize_product(product, sold_count, avg_rating, min_price)
            for product, sold_count, avg_rating, min_price in pagination.items
        ]

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": pagination.total,
            "total_pages": pagination.pages or 0,
            "current_filter": filter_by,
            "current_sort": applied_sort,
        }

    @staticmethod
    def follow(shop_id: int, user_id: int | None) -> dict:
        shop = Shop.query.get(shop_id)
        if not shop:
            raise NotFoundError("Không tìm thấy shop")
        if not user_id:
            raise UnauthorizedError("Vui lòng đăng nhập để theo dõi shop")
        if user_id == shop.owner_id:
            raise ValidationError("Không thể theo dõi shop của chính bạn")

        follow = ShopFollow.query.filter_by(shop_id=shop_id, user_id=user_id).first()
        if not follow:
            follow = ShopFollow(shop_id=shop_id, user_id=user_id)
            db.session.add(follow)
            db.session.commit()

        return {
            "is_following": True,
            "followers_count": ShopFollow.query.filter_by(shop_id=shop_id).count(),
        }

    @staticmethod
    def unfollow(shop_id: int, user_id: int | None) -> dict:
        shop = Shop.query.get(shop_id)
        if not shop:
            raise NotFoundError("Không tìm thấy shop")
        if not user_id:
            raise UnauthorizedError("Vui lòng đăng nhập để bỏ theo dõi shop")
        if user_id == shop.owner_id:
            raise ValidationError("Shop của bạn không có trạng thái theo dõi")

        follow = ShopFollow.query.filter_by(shop_id=shop_id, user_id=user_id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

        return {
            "is_following": False,
            "followers_count": ShopFollow.query.filter_by(shop_id=shop_id).count(),
        }