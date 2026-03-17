from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.models import Category, FlashSale, OrderItem, Product, ProductVariant
from app.models import Review
from app.core.enums.product_status import ProductStatus

class HomeService:
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
    def _to_float(value: Decimal | None) -> float:
        if value is None:
            return 0.0
        return float(value)

    @staticmethod
    def _product_card_payload(
        product: Product,
        sold_count: int = 0,
        discount_percent: int | None = None,
        sale_price: Decimal | None = None,
    ) -> dict:

        image_url = HomeService._normalize_asset_url(product.thumbnail)

        variants = product.variants
        price = min(v.price for v in variants) if variants else 0
        avg_rating = (
            Review.query.with_entities(func.avg(Review.rating))
            .filter(Review.product_id == product.id)
            .scalar()
        )

        avg_rating = float(avg_rating) if avg_rating else 0.0
        return {
            "id": product.id,
            "name": product.name,
            "price": HomeService._to_float(price),
            "rating": round(avg_rating, 1),
            "sold": int(sold_count),
            "image": image_url,
            "discount_percent": discount_percent,
            "sale_price": HomeService._to_float(sale_price) if sale_price is not None else None,
            "product_url": f"/shop/{product.id}",
        }

    @staticmethod
    def _fallback_context() -> dict:
        sample_products = [
            {
                "id": i,
                "name": f"Sản phẩm gợi ý {i}",
                "price": 199000 + i * 5000,
                "rating": 0.0,
                "sold": 0,
                "image": "/static/images/no-image.png",
                "discount_percent": 15 if i % 4 == 0 else None,
                "sale_price": int((199000 + i * 5000) * 0.85) if i % 4 == 0 else None,
                "product_url": f"/shop/{i}",
            }
            for i in range(1, 9)
        ]
        return {
            "search_suggestions": ["điện thoại", "tai nghe", "quạt mini", "bàn phím cơ"],
            "hero_banners": [
                {
                    "title": "Sale 50%",
                    "subtitle": "Săn deal cực sốc hôm nay",
                    "link": "/shop",
                    "variant": "main",
                },
                {
                    "title": "Free ship toàn quốc",
                    "subtitle": "Áp dụng cho đơn từ 0đ",
                    "link": "/shop",
                    "variant": "small",
                },
                {
                    "title": "Flash sale mỗi ngày",
                    "subtitle": "Giảm sâu theo khung giờ",
                    "link": "/shop",
                    "variant": "small",
                },
            ],
            "feature_items": [
                {"icon": "💥", "label": "Deal 1K", "link": "#"},
                {"icon": "⚡", "label": "Flash Sale", "link": "#"},
                {"icon": "🚚", "label": "Freeship", "link": "#"},
                {"icon": "🏬", "label": "Mall", "link": "#"},
                {"icon": "🎟️", "label": "Voucher", "link": "#"},
            ],
            "categories": [
                {"name": "Phone"}, {"name": "Laptop"}, {"name": "Tablet"}, {"name": "Camera"},
                {"name": "Audio"}, {"name": "Watch"}, {"name": "Gaming"}, {"name": "Accessories"},
                {"name": "SmartHome"}, {"name": "Gia dụng"}, {"name": "Thời trang"}, {"name": "Sức khỏe"},
                {"name": "Mẹ & Bé"}, {"name": "Nhà cửa"}, {"name": "Sách"}, {"name": "Thể thao"},
            ],
            "flash_sale": {
                "ends_at_iso": None,
                "items": [],
            },
            "top_search_items": [],
            "recommended_items": [],
            "promotion_banners": [
                {"title": "Sale Laptop 30%", "subtitle": "Hiệu năng cao giá tốt", "link": "/shop"},
                {"title": "Phụ kiện gaming", "subtitle": "Combo gear siêu hời", "link": "/shop"},
            ],
        }

    @staticmethod
    def build_home_context() -> dict:
        base = HomeService._fallback_context()
        now = datetime.now(timezone.utc)

        try:
            categories = Category.query.order_by(Category.name.asc()).limit(16).all()
            if categories:
                base["categories"] = [{"name": c.name} for c in categories]

            sold_subquery = (
                OrderItem.query.with_entities(
                    OrderItem.product_id.label("product_id"),
                    func.coalesce(func.sum(OrderItem.quantity), 0).label("sold"),
                )
                .group_by(OrderItem.product_id)
                .subquery()
            )

            top_rows = (
                Product.query
                .filter(Product.status == ProductStatus.ACTIVE)
                .outerjoin(sold_subquery, Product.id == sold_subquery.c.product_id)
                .add_columns(func.coalesce(sold_subquery.c.sold, 0).label("sold"))
                .order_by(func.coalesce(sold_subquery.c.sold, 0).desc(), Product.created_at.desc())
                .limit(8)
                .all()
            )

            if top_rows:
                top_cards = [
                    HomeService._product_card_payload(product, sold_count=sold)
                    for product, sold in top_rows
                ]
                base["top_search_items"] = top_cards[:4]
                base["recommended_items"] = top_cards

            flash_sales = (
                FlashSale.query
                .filter(
                    FlashSale.is_active.is_(True),
                    FlashSale.start_time <= now,
                    FlashSale.end_time >= now,
                )
                .order_by(FlashSale.end_time.asc())
                .limit(4)
                .all()
            )
            flash_cards = []
            flash_map_by_product_id: dict[int, dict] = {}
            flash_end = None
            for sale in flash_sales:
                variant = ProductVariant.query.get(sale.variant_id)
                if not variant:
                    continue

                product = Product.query.get(variant.product_id)
                if not product:
                    continue
                sold_count = sale.sold_count or 0
                sale_price = variant.price * (Decimal(1) - Decimal(sale.discount_percent) / Decimal(100))
                card_payload = HomeService._product_card_payload(
                    product,
                    sold_count=sold_count,
                    discount_percent=sale.discount_percent,
                    sale_price=sale_price,
                )
                flash_cards.append(card_payload)
                flash_map_by_product_id[product.id] = {
                    "discount_percent": sale.discount_percent,
                    "sale_price": sale_price,
                }
                if flash_end is None or sale.end_time < flash_end:
                    flash_end = sale.end_time

            
            base["flash_sale"]["items"] = flash_cards
            if flash_end:
                base["flash_sale"]["ends_at_iso"] = flash_end.replace(tzinfo=timezone.utc).isoformat()
            if base.get("recommended_items") and flash_map_by_product_id:
                for item in base["recommended_items"]:
                    flash_info = flash_map_by_product_id.get(item.get("id"))
                    if not flash_info:
                        continue
                    item["discount_percent"] = flash_info.get("discount_percent")
                    item["sale_price"] = HomeService._to_float(flash_info.get("sale_price"))

        except SQLAlchemyError:
            return base

        return base