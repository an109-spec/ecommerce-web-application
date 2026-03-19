from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from flask import session
from app.models.flash_sale import FlashSale
from app.models.product import Product, ProductVariant
from app.models.promotion import Promotion
from app.models.voucher import Voucher
from app.common.exceptions import AppException

class CartService:
    SESSION_KEY = "cart"

    @staticmethod
    def get_cart() -> dict[str, Any]:
        cart = session.get(CartService.SESSION_KEY)

        if not cart:
            cart = {"items": {}, "applied_vouchers": {}}
            session[CartService.SESSION_KEY] = cart
        cart.setdefault("items", {})
        cart.setdefault("applied_vouchers", {})

        return cart

    # =========================
    # ADD
    # =========================

    @staticmethod
    def add_to_cart(
        product_id: int,
        quantity: int,
        *,
        variant_id: int | None = None,
        size: str | None = None,
        color: str | None = None,
    ) -> dict[str, Any]:
        if quantity <= 0:
            raise ValueError("Số lượng phải lớn hơn 0")

        variant = CartService._resolve_variant(product_id, variant_id=variant_id, size=size, color=color)
        if not variant:
            raise ValueError("Không tìm thấy phân loại sản phẩm phù hợp")

        cart = CartService.get_cart()
        items = cart["items"]
        variant_key = str(variant.id)
        current_qty = int(items.get(variant_key, {}).get("quantity", 0))
        new_qty = current_qty + int(quantity)

        if new_qty > int(variant.stock or 0):
            raise ValueError("Số lượng vượt quá tồn kho")

        items[variant_key] = {
            "product_id": variant.product_id,
            "variant_id": variant.id,
            "quantity": new_qty,
        }
        CartService._mark_session_dirty()
        return CartService.get_mini_cart()

    @staticmethod
    def remove_item(variant_id: int) -> dict[str, Any]:
        cart = CartService.get_cart()
        removed = cart["items"].pop(str(variant_id), None)
        if removed:
            CartService._cleanup_applied_vouchers(cart)
            CartService._mark_session_dirty()
        return CartService.build_cart_payload()

    @staticmethod
    def update_item(
        current_variant_id: int,
        *,
        quantity: int,
        variant_id: int | None = None,
        size: str | None = None,
        color: str | None = None,
    ) -> dict[str, Any]:
        cart = CartService.get_cart()
        items = cart["items"]
        current_key = str(current_variant_id)
        current_entry = items.get(current_key)
        if not current_entry:
            raise ValueError("Sản phẩm không tồn tại trong giỏ hàng")

        if quantity <= 0:
            return CartService.remove_item(current_variant_id)

        product_id = int(current_entry["product_id"])
        target_variant = CartService._resolve_variant(product_id, variant_id=variant_id, size=size, color=color)
        if not target_variant:
            raise ValueError("Không tìm thấy phân loại sản phẩm phù hợp")

        if quantity > int(target_variant.stock or 0):
            raise ValueError("Số lượng vượt quá tồn kho")

        target_key = str(target_variant.id)
        if target_key != current_key and target_key in items:
            merged_qty = int(items[target_key]["quantity"]) + int(quantity)
            if merged_qty > int(target_variant.stock or 0):
                raise ValueError("Số lượng vượt quá tồn kho")
            items[target_key]["quantity"] = merged_qty
            del items[current_key]
        else:
            if target_key != current_key:
                del items[current_key]
            items[target_key] = {
                "product_id": product_id,
                "variant_id": target_variant.id,
                "quantity": int(quantity),
            }

        CartService._cleanup_applied_vouchers(cart)
        CartService._mark_session_dirty()
        return CartService.build_cart_payload()

    @staticmethod
    def clear_cart() -> None:
        session.pop(CartService.SESSION_KEY, None)
        session.modified = True

    @staticmethod
    def apply_voucher(shop_id: int, voucher_id: int) -> dict[str, Any]:
        cart = CartService.get_cart()
        payload = CartService.build_cart_payload()
        shop_payload = next((shop for shop in payload["shops"] if int(shop["shop_id"]) == int(shop_id)), None)
        if not shop_payload:
            raise ValueError("Shop không có sản phẩm trong giỏ hàng")

        voucher = CartService._get_valid_voucher(voucher_id, shop_id)
        if not voucher:
            raise ValueError("Voucher không hợp lệ")

        subtotal = Decimal(str(shop_payload["shop_subtotal_raw"]))
        if subtotal < Decimal(str(voucher.min_order_value or 0)):
            raise AppException("Chưa đạt giá trị đơn tối thiểu để áp dụng voucher", status_code=400)

        cart["applied_vouchers"][str(shop_id)] = int(voucher.id)
        CartService._mark_session_dirty()
        return CartService.build_cart_payload()

    @staticmethod
    def get_summary() -> dict[str, Any]:
        payload = CartService.build_cart_payload()
        return {
            "subtotal": payload["cart_subtotal"],
            "discount": payload["voucher_discount_total"],
            "total": payload["cart_total"],
            "items_count": payload["cart_item_count"],
        }
    @staticmethod
    def get_mini_cart() -> dict[str, Any]:
        payload = CartService.build_cart_payload()
        return {
            "cart_item_count": payload["cart_item_count"],
            "cart_subtotal": payload["cart_subtotal"],
            "items": payload["mini_items"],
        }

    @staticmethod
    def get_cart_item_details(variant_id: int) -> dict[str, Any]:
        cart = CartService.get_cart()
        entry = cart["items"].get(str(variant_id))
        if not entry:
            raise ValueError("Sản phẩm không tồn tại trong giỏ hàng")

        variant = ProductVariant.query.get(variant_id)
        if not variant or not variant.product:
            raise ValueError("Không tìm thấy phân loại sản phẩm")

        pricing = CartService._get_variant_pricing(variant)
        product = variant.product
        return {
            "variant_id": variant.id,
            "product_id": product.id,
            "product_name": product.name,
            "product_image": CartService._image_url(variant.image_url or product.thumbnail),
            "quantity": int(entry.get("quantity", 1)),
            "variant_stock": int(variant.stock or 0),
            "variant_price": CartService._money(pricing["variant_price"]),
            "original_price": CartService._money(pricing["variant_price"]),
            "flash_price": CartService._money(pricing["flash_price"]) if pricing["flash_price"] is not None else None,
            "flash_discount": CartService._money(pricing["flash_discount"]),
            "promotion_discount": CartService._money(pricing["promotion_discount"]),
            "effective_price": CartService._money(pricing["effective_price"]),
            "selected": {
                "size": CartService._variant_attr(variant, "size"),
                "color": CartService._variant_attr(variant, "color"),
            },
            "size_options": CartService._collect_variant_options(product, "size"),
            "color_options": CartService._collect_variant_options(product, "color"),
        }

    @staticmethod
    def build_cart_payload() -> dict[str, Any]:
        cart = CartService.get_cart()
        items = cart["items"]
        applied_vouchers = cart.get("applied_vouchers", {})

        shops_map: OrderedDict[int, dict[str, Any]] = OrderedDict()
        mini_items: list[dict[str, Any]] = []
        cart_item_count = 0
        cart_subtotal_raw = Decimal("0")
        voucher_discount_total_raw = Decimal("0")
        shipping_total_raw = Decimal("0")

        for entry in items.values():
            variant = ProductVariant.query.get(entry.get("variant_id"))
            if not variant or not variant.product or not variant.product.shop:
                continue

            item_payload = CartService._serialize_item(variant, int(entry.get("quantity", 1)))
            cart_item_count += item_payload["quantity"]
            cart_subtotal_raw += Decimal(str(item_payload["item_total_raw"]))
            mini_items.append(
                {
                    "variant_id": item_payload["variant_id"],
                    "product_name": item_payload["product_name"],
                    "product_image": item_payload["product_image"],
                    "price": item_payload["effective_price"],
                    "quantity": item_payload["quantity"],
                    "item_total": item_payload["item_total"],
                }
            )

            shop_id = int(item_payload["shop_id"])
            shop_group = shops_map.setdefault(
                shop_id,
                {
                    "shop_id": shop_id,
                    "shop_name": item_payload["shop_name"],
                    "shipping_fee_raw": item_payload["shipping_fee_raw"],
                    "shipping_fee": item_payload["shipping_fee"],
                    "items": [],
                    "available_vouchers": CartService._list_shop_vouchers(shop_id),
                },
            )
            shop_group["items"].append(item_payload)

        for shop_id, shop_group in shops_map.items():
            shop_subtotal_raw = sum((Decimal(str(item["item_total_raw"])) for item in shop_group["items"]), Decimal("0"))
            shop_group["shop_subtotal_raw"] = CartService._money(shop_subtotal_raw)
            shop_group["shop_subtotal"] = CartService._money(shop_subtotal_raw)

            voucher = None
            voucher_discount_raw = Decimal("0")
            applied_voucher_id = applied_vouchers.get(str(shop_id))
            if applied_voucher_id:
                voucher = CartService._get_valid_voucher(applied_voucher_id, shop_id)
                if voucher and shop_subtotal_raw >= Decimal(str(voucher.min_order_value or 0)):
                    voucher_discount_raw = CartService._calculate_voucher_discount(shop_subtotal_raw, voucher)
                else:
                    cart["applied_vouchers"].pop(str(shop_id), None)
                    voucher = None

            shipping_fee_raw = Decimal(str(shop_group["shipping_fee_raw"]))
            shop_total_raw = max(shop_subtotal_raw - voucher_discount_raw + shipping_fee_raw, Decimal("0"))

            voucher_discount_total_raw += voucher_discount_raw
            shipping_total_raw += shipping_fee_raw

            shop_group["voucher"] = CartService._serialize_applied_voucher(voucher, voucher_discount_raw)
            shop_group["shop_voucher_discount"] = CartService._money(voucher_discount_raw)
            shop_group["shop_total_raw"] = CartService._money(shop_total_raw)
            shop_group["shop_total"] = CartService._money(shop_total_raw)

        cart_total_raw = max(cart_subtotal_raw - voucher_discount_total_raw + shipping_total_raw, Decimal("0"))

        CartService._cleanup_applied_vouchers(cart)

        return {
            "cart_item_count": cart_item_count,
            "cart_subtotal_raw": CartService._money(cart_subtotal_raw),
            "cart_subtotal": CartService._money(cart_subtotal_raw),
            "voucher_discount_total_raw": CartService._money(voucher_discount_total_raw),
            "voucher_discount_total": CartService._money(voucher_discount_total_raw),
            "shipping_total_raw": CartService._money(shipping_total_raw),
            "shipping_total": CartService._money(shipping_total_raw),
            "cart_total_raw": CartService._money(cart_total_raw),
            "cart_total": CartService._money(cart_total_raw),
            "shops": list(shops_map.values()),
            "mini_items": mini_items,
        }
    @staticmethod
    def _serialize_item(variant: ProductVariant, quantity: int) -> dict[str, Any]:
        pricing = CartService._get_variant_pricing(variant)
        product = variant.product
        shop = product.shop if product else None
        item_total_raw = pricing["effective_price"] * quantity

        return {
            "product_id": product.id,
            "variant_id": variant.id,
            "product_name": product.name,
            "product_image": CartService._image_url(variant.image_url or product.thumbnail),
            "shop_id": shop.id if shop else None,
            "shop_name": shop.name if shop else "OneShop",
            "size": CartService._variant_attr(variant, "size"),
            "color": CartService._variant_attr(variant, "color"),
            "original_price": CartService._money(pricing["variant_price"]),
            "variant_price": CartService._money(pricing["variant_price"]),
            "flash_price": CartService._money(pricing["flash_price"]) if pricing["flash_price"] is not None else None,
            "flash_discount": CartService._money(pricing["flash_discount"]),
            "promotion_discount": CartService._money(pricing["promotion_discount"]),
            "effective_price": CartService._money(pricing["effective_price"]),
            "quantity": int(quantity),
            "stock": int(variant.stock or 0),
            "item_total_raw": CartService._money(item_total_raw),
            "item_total": CartService._money(item_total_raw),
            "shipping_fee_raw": CartService._money(Decimal(str(shop.shipping_fee or 0)) if shop else Decimal("0")),
            "shipping_fee": CartService._money(Decimal(str(shop.shipping_fee or 0)) if shop else Decimal("0")),
        }

    @staticmethod
    def _get_variant_pricing(variant: ProductVariant) -> dict[str, Decimal | None]:
        base_price = Decimal(str(variant.price or 0))
        flash_sale = CartService._get_active_flash_sale(variant.id)
        promotion = CartService._get_active_promotion(variant.id)

        flash_discount = Decimal("0")
        flash_price = None
        if flash_sale:
            flash_discount = (base_price * Decimal(str(flash_sale.discount_percent or 0)) / Decimal("100")).quantize(Decimal("0.01"))
            flash_price = max(base_price - flash_discount, Decimal("0"))

        promotion_discount = Decimal("0")
        if promotion:
            promotion_discount = (base_price * Decimal(str(promotion.discount_percent or 0)) / Decimal("100")).quantize(Decimal("0.01"))

        effective_price = max(base_price - flash_discount - promotion_discount, Decimal("0"))

        return {
            "variant_price": base_price,
            "flash_discount": flash_discount,
            "flash_price": flash_price,
            "promotion_discount": promotion_discount,
            "effective_price": effective_price,
        }
    @staticmethod
    def _resolve_variant(
        product_id: int,
        *,
        variant_id: int | None = None,
        size: str | None = None,
        color: str | None = None,
    ) -> ProductVariant | None:
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Không tìm thấy sản phẩm")

        variants = product.variants or []
        if variant_id:
            variant = next((item for item in variants if int(item.id) == int(variant_id)), None)
            if variant:
                return variant

        normalized_size = CartService._normalize_option(size)
        normalized_color = CartService._normalize_option(color)

        if not normalized_size and not normalized_color:
            if len(variants) == 1:
                return variants[0]
            return next((item for item in variants if int(item.stock or 0) > 0), variants[0] if variants else None)

        for variant in variants:
            variant_size = CartService._normalize_option(CartService._variant_attr(variant, "size"))
            variant_color = CartService._normalize_option(CartService._variant_attr(variant, "color"))
            size_ok = not normalized_size or variant_size == normalized_size
            color_ok = not normalized_color or variant_color == normalized_color
            if size_ok and color_ok:
                return variant
        return None

    @staticmethod
    def _variant_attr(variant: ProductVariant, attr_name: str) -> str:
        aliases = {
            "size": {"size", "kích thước", "kich thuoc"},
            "color": {"color", "màu", "mau"},
        }
        expected = aliases.get(attr_name, {attr_name.lower()})
        for attr in variant.variant_attributes or []:
            if CartService._normalize_option(attr.name) in expected:
                return (attr.value or "").strip()
        return ""

    @staticmethod
    def _collect_variant_options(product: Product, attr_name: str) -> list[str]:
        values = {
            CartService._variant_attr(variant, attr_name)
            for variant in (product.variants or [])
            if CartService._variant_attr(variant, attr_name)
        }
        return sorted(values)

    @staticmethod
    def _get_active_flash_sale(variant_id: int) -> FlashSale | None:
        now = datetime.now(timezone.utc)
        return (
            FlashSale.query.filter(
                FlashSale.variant_id == variant_id,
                FlashSale.is_active.is_(True),
                FlashSale.start_time <= now,
                FlashSale.end_time >= now,
                FlashSale.sold_count < FlashSale.stock_limit,
            )
            .order_by(FlashSale.discount_percent.desc(), FlashSale.end_time.asc())
            .first()
        )

    @staticmethod
    def _get_active_promotion(variant_id: int) -> Promotion | None:
        now = datetime.now(timezone.utc)
        return (
            Promotion.query.filter(
                Promotion.variant_id == variant_id,
                Promotion.is_active.is_(True),
                Promotion.start_time <= now,
                Promotion.end_time >= now,
            )
            .order_by(Promotion.discount_percent.desc(), Promotion.end_time.asc())
            .first()
        )

    @staticmethod
    def _get_valid_voucher(voucher_id: int, shop_id: int) -> Voucher | None:
        now = datetime.now(timezone.utc)
        return (
            Voucher.query.filter(
                Voucher.id == voucher_id,
                Voucher.shop_id == shop_id,
                Voucher.is_active.is_(True),
                Voucher.start_time <= now,
                Voucher.end_time >= now,
                Voucher.used_count < Voucher.usage_limit,
            )
            .first()
        )

    @staticmethod
    def _list_shop_vouchers(shop_id: int) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        vouchers = (
            Voucher.query.filter(
                Voucher.shop_id == shop_id,
                Voucher.is_active.is_(True),
                Voucher.start_time <= now,
                Voucher.end_time >= now,
                Voucher.used_count < Voucher.usage_limit,
            )
            .order_by(Voucher.discount_value.desc(), Voucher.id.desc())
            .all()
        )
        return [
            {
                "voucher_id": voucher.id,
                "voucher_code": voucher.code,
                "voucher_name": voucher.name,
                "discount_type": voucher.discount_type,
                "voucher_discount": voucher.discount_value,
                "voucher_min_order": voucher.min_order_value,
            }
            for voucher in vouchers
        ]

    @staticmethod
    def _calculate_voucher_discount(subtotal: Decimal, voucher: Voucher) -> Decimal:
        if (voucher.discount_type or "").lower() == "percent":
            discount = subtotal * Decimal(str(voucher.discount_value or 0)) / Decimal("100")
        else:
            discount = Decimal(str(voucher.discount_value or 0))
        return min(subtotal, discount.quantize(Decimal("0.01")))

    @staticmethod
    def _serialize_applied_voucher(voucher: Voucher | None, discount_raw: Decimal) -> dict[str, Any] | None:
        if not voucher:
            return None

        return {
            "voucher_id": voucher.id,
            "voucher_code": voucher.code,
            "voucher_name": voucher.name,
            "voucher_discount": CartService._money(discount_raw),
            "voucher_min_order": CartService._money(Decimal(str(voucher.min_order_value or 0))),
        }

    @staticmethod
    def _cleanup_applied_vouchers(cart: dict[str, Any]) -> None:
        valid_shop_ids = set()
        for entry in cart.get("items", {}).values():
            variant = ProductVariant.query.get(entry.get("variant_id"))
            if variant and variant.product and variant.product.shop_id:
                valid_shop_ids.add(str(variant.product.shop_id))

        for shop_id in list(cart.get("applied_vouchers", {}).keys()):
            if shop_id not in valid_shop_ids:
                cart["applied_vouchers"].pop(shop_id, None)

    @staticmethod
    def _normalize_option(value: str | None) -> str:
        return (value or "").strip().lower()

    @staticmethod
    def _image_url(src: str | None) -> str:
        if not src:
            return "/static/images/no-image.png"
        if src.startswith(("http://", "https://", "/")):
            return src
        if src.startswith("static/"):
            return f"/{src}"
        return f"/static/{src}"

    @staticmethod
    def _money(value: Decimal | int | float | str | None) -> float:
        return float(Decimal(str(value or 0)).quantize(Decimal("0.01")))

    @staticmethod
    def _mark_session_dirty() -> None:
        session.modified = True