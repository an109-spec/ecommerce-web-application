from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from flask import session

from app.common.exceptions import NotFoundError, ValidationError
from app.extensions.db import db
from app.models import FlashSale, Order, OrderItem, Product, ProductVariant, Promotion, Voucher
from app.modules.cart.service import CartService
from app.modules.user.service import UserService
from app.core.enums.order_status import OrderStatus, PaymentMethod
import uuid

class CheckoutService:
    SESSION_KEY = "checkout"

    SHIPPING_METHODS = OrderedDict(
        [
            (
                "fast",
                {
                    "label": "Nhanh",
                    "shop_flag": "shipping_fast",
                    "variant_fee": "shipping_fast_fee",
                },
            ),
            (
                "same_day",
                {
                    "label": "Same Day",
                    "shop_flag": "shipping_same_day",
                    "variant_fee": "shipping_same_day_fee",
                },
            ),
            (
                "express",
                {
                    "label": "Express",
                    "shop_flag": "shipping_express",
                    "variant_fee": "shipping_express_fee",
                },
            ),
            (
                "pickup",
                {
                    "label": "Pickup",
                    "shop_flag": "shipping_pickup_point",
                    "variant_fee": "shipping_pickup_fee",
                },
            ),
            (
                "bulky",
                {
                    "label": "Bulky",
                    "shop_flag": "shipping_bulky",
                    "variant_fee": "shipping_bulky_fee",
                },
            ),
        ]
    )

    @staticmethod
    def init_checkout(user_id: int, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        state = CheckoutService._normalize_state(user_id, payload)
        CheckoutService._save_state(state)
        return CheckoutService.build_checkout_payload(user_id)

    @staticmethod
    def get_current_checkout(user_id: int, *, auto_init_from_cart: bool = True) -> dict[str, Any]:
        state = CheckoutService._get_state()
        if not state or not state.get("items"):
            if auto_init_from_cart:
                return CheckoutService.init_checkout(user_id, None)
            raise ValidationError("Chưa có dữ liệu checkout")
        return CheckoutService.build_checkout_payload(user_id)

    @staticmethod
    def apply_voucher(user_id: int, shop_id: int, *, voucher_id: int | None = None, voucher_code: str | None = None) -> dict[str, Any]:
        state = CheckoutService._require_state()
        shop_id = int(shop_id)
        payload = CheckoutService.build_checkout_payload(user_id)
        shop_payload = next((shop for shop in payload["shops"] if int(shop["shop_id"]) == shop_id), None)
        if not shop_payload:
            raise ValidationError("Shop không có trong checkout")

        voucher = None
        if voucher_id:
            voucher = CheckoutService._get_valid_voucher(voucher_id=voucher_id, shop_id=shop_id)
        elif voucher_code:
            voucher = CheckoutService._get_valid_voucher(voucher_code=voucher_code, shop_id=shop_id)
        else:
            raise ValidationError("Thiếu thông tin voucher")

        if not voucher:
            raise ValidationError("Voucher không hợp lệ")

        subtotal = Decimal(str(shop_payload["shop_subtotal_raw"]))
        if subtotal < Decimal(str(voucher.min_order_value or 0)):
            raise ValidationError("Chưa đạt giá trị đơn tối thiểu để áp dụng voucher")

        state.setdefault("shop_vouchers", {})[str(shop_id)] = int(voucher.id)
        CheckoutService._save_state(state)
        return CheckoutService.build_checkout_payload(user_id)

    @staticmethod
    def update_shipping_method(user_id: int, shop_id: int, shipping_method: str) -> dict[str, Any]:
        state = CheckoutService._require_state()
        shipping_method = (shipping_method or "").strip().lower()
        if shipping_method not in CheckoutService.SHIPPING_METHODS:
            raise ValidationError("Phương thức vận chuyển không hợp lệ")

        payload = CheckoutService.build_checkout_payload(user_id)
        shop_payload = next((shop for shop in payload["shops"] if int(shop["shop_id"]) == int(shop_id)), None)
        if not shop_payload:
            raise ValidationError("Shop không có trong checkout")
        if shipping_method not in {item["code"] for item in shop_payload["shipping_methods"]}:
            raise ValidationError("Shop không hỗ trợ phương thức vận chuyển này")

        state.setdefault("shipping_methods", {})[str(shop_id)] = shipping_method
        CheckoutService._save_state(state)
        return CheckoutService.build_checkout_payload(user_id)

    @staticmethod
    def update_payment_method(user_id: int, payment_method: str) -> dict[str, Any]:
        state = CheckoutService._require_state()
        normalized = (payment_method or "").strip().upper()
        if normalized not in {PaymentMethod.COD.value, PaymentMethod.VNPAY.value}:
            raise ValidationError("Phương thức thanh toán không hợp lệ")
        state["payment_method"] = normalized
        CheckoutService._save_state(state)
        return CheckoutService.build_checkout_payload(user_id)

    @staticmethod
    def update_address(user_id: int, address_id: str) -> dict[str, Any]:
        state = CheckoutService._require_state()
        address = UserService.get_address_by_id(user_id, address_id)
        state["address_id"] = address["id"]
        CheckoutService._save_state(state)
        return CheckoutService.build_checkout_payload(user_id)

    @staticmethod
    def confirm_checkout(user_id: int) -> dict[str, Any]:
        state = CheckoutService._require_state()
        payload = CheckoutService.build_checkout_payload(user_id)
        address = payload.get("address")
        if not address:
            raise ValidationError("Vui lòng chọn địa chỉ nhận hàng")

        payment_method_raw = (state.get("payment_method") or "").strip().upper()
        if payment_method_raw not in {PaymentMethod.COD.value, PaymentMethod.VNPAY.value}:
            raise ValidationError("Vui lòng chọn phương thức thanh toán")
        payment_method = PaymentMethod(payment_method_raw)

        order = Order(
            user_id=user_id,
            total_price=Decimal(str(payload["total_raw"])),
            subtotal=Decimal(str(payload["subtotal_raw"])),
            shipping_fee=Decimal(str(payload["shipping_total_raw"])),
            status=OrderStatus.PENDING,
            payment_method=payment_method,
            order_code=CheckoutService._generate_order_code(),
        )
        db.session.add(order)
        db.session.flush()

        for shop in payload["shops"]:
            voucher_data = shop.get("voucher")
            if voucher_data:
                voucher = db.session.get(Voucher, int(voucher_data["voucher_id"]))
                if not voucher or not CheckoutService._get_valid_voucher(voucher_id=voucher.id, shop_id=shop["shop_id"]):
                    raise ValidationError("Voucher không còn hợp lệ")
                voucher.used_count = int(voucher.used_count or 0) + 1

            for item in shop["items"]:
                variant = db.session.get(ProductVariant, int(item["variant_id"]))
                if not variant or not variant.product:
                    raise NotFoundError("Không tìm thấy phân loại sản phẩm")
                quantity = int(item["quantity"])
                if quantity > int(variant.stock or 0):
                    raise ValidationError(f"Sản phẩm {variant.product.name} không đủ tồn kho")

                price = Decimal(str(item["effective_price_raw"]))
                subtotal = Decimal(str(item["item_total_raw"]))
                db.session.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=variant.product_id,
                        price=price,
                        quantity=quantity,
                        subtotal=subtotal,
                        product_name=variant.product.name or "",
                        product_thumbnail=variant.image_url or variant.product.thumbnail,
                    )
                )
                variant.stock = int(variant.stock or 0) - quantity

                flash_sale = CheckoutService._get_active_flash_sale(variant.id)
                if flash_sale:
                    flash_sale.sold_count = int(flash_sale.sold_count or 0) + quantity

        db.session.commit()
        CheckoutService._cleanup_after_confirm(state)

        redirect_url = f"/payment/success/{order.id}"
        if payment_method == PaymentMethod.VNPAY:
            redirect_url = f"/payment/select/{order.id}"

        return {
            "message": "Đặt hàng thành công",
            "order_id": order.id,
            "redirect_url": redirect_url,
        }
    @staticmethod
    def _generate_order_code() -> str:
        return uuid.uuid4().hex[:12].upper()


    @staticmethod
    def build_checkout_payload(user_id: int) -> dict[str, Any]:
        state = CheckoutService._require_state()
        normalized_state = CheckoutService._normalize_state(user_id, state)
        CheckoutService._save_state(normalized_state)
        state = normalized_state

        addresses = UserService.get_addresses(user_id)
        selected_address_id = state.get("address_id")
        selected_address = next((item for item in addresses if item["id"] == selected_address_id), None)
        if not selected_address:
            selected_address = next((item for item in addresses if item.get("is_default")), None)
            if selected_address:
                state["address_id"] = selected_address["id"]
                CheckoutService._save_state(state)

        shops_map: OrderedDict[int, dict[str, Any]] = OrderedDict()
        subtotal_raw = Decimal("0")
        shipping_total_raw = Decimal("0")
        voucher_discount_total_raw = Decimal("0")

        for item_entry in state.get("items", []):
            variant = CheckoutService._resolve_variant(item_entry)
            quantity = int(item_entry["quantity"])
            if quantity > int(variant.stock or 0):
                raise ValidationError(f"Sản phẩm {variant.product.name} vượt quá tồn kho")

            serialized_item = CheckoutService._serialize_item(variant, quantity)
            subtotal_raw += Decimal(str(serialized_item["item_total_raw"]))

            shop_id = int(serialized_item["shop_id"] or 0)
            shop_group = shops_map.setdefault(
                shop_id,
                {
                    "shop_id": shop_id,
                    "shop_name": serialized_item["shop_name"],
                    "items": [],
                    "available_vouchers": CartService._list_shop_vouchers(shop_id),
                    "shipping_methods": [],
                },
            )
            shop_group["items"].append(serialized_item)

        for shop_id, shop_group in shops_map.items():
            shipping_methods = CheckoutService._build_shipping_methods(shop_group["items"])
            if not shipping_methods:
                shipping_methods = [
                    {
                        "code": "fast",
                        "label": "Nhanh",
                        "fee_raw": 0.0,
                        "fee": 0.0,
                        "selected": True,
                    }
                ]

            selected_method = state.setdefault("shipping_methods", {}).get(str(shop_id))
            available_codes = {method["code"] for method in shipping_methods}
            if selected_method not in available_codes:
                selected_method = shipping_methods[0]["code"]
                state["shipping_methods"][str(shop_id)] = selected_method

            for method in shipping_methods:
                method["selected"] = method["code"] == selected_method

            shipping_fee_raw = next(
                Decimal(str(method["fee_raw"])) for method in shipping_methods if method["code"] == selected_method
            )
            shipping_total_raw += shipping_fee_raw

            shop_subtotal_raw = sum((Decimal(str(item["item_total_raw"])) for item in shop_group["items"]), Decimal("0"))
            voucher_discount_raw = Decimal("0")
            voucher = None
            voucher_id = state.setdefault("shop_vouchers", {}).get(str(shop_id))
            if voucher_id:
                voucher = CheckoutService._get_valid_voucher(voucher_id=int(voucher_id), shop_id=shop_id)
                if voucher and shop_subtotal_raw >= Decimal(str(voucher.min_order_value or 0)):
                    voucher_discount_raw = CartService._calculate_voucher_discount(shop_subtotal_raw, voucher)
                else:
                    state["shop_vouchers"].pop(str(shop_id), None)
                    voucher = None

            voucher_discount_total_raw += voucher_discount_raw
            shop_total_raw = max(shop_subtotal_raw - voucher_discount_raw + shipping_fee_raw, Decimal("0"))

            shop_group["shop_subtotal_raw"] = CheckoutService._money(shop_subtotal_raw)
            shop_group["shop_subtotal"] = CheckoutService._money(shop_subtotal_raw)
            shop_group["shipping_fee_raw"] = CheckoutService._money(shipping_fee_raw)
            shop_group["shipping_fee"] = CheckoutService._money(shipping_fee_raw)
            shop_group["shop_voucher_discount_raw"] = CheckoutService._money(voucher_discount_raw)
            shop_group["shop_voucher_discount"] = CheckoutService._money(voucher_discount_raw)
            shop_group["shop_total_raw"] = CheckoutService._money(shop_total_raw)
            shop_group["shop_total"] = CheckoutService._money(shop_total_raw)
            shop_group["voucher"] = CartService._serialize_applied_voucher(voucher, voucher_discount_raw)
            shop_group["shipping_methods"] = shipping_methods
            shop_group["selected_shipping_method"] = selected_method

        total_raw = max(subtotal_raw - voucher_discount_total_raw + shipping_total_raw, Decimal("0"))
        CheckoutService._save_state(state)

        return {
            "address": selected_address,
            "addresses": addresses,
            "payment_method": state.get("payment_method", PaymentMethod.COD.value),
            "payment_methods": [
                {"code": PaymentMethod.COD.value, "label": "Thanh toán khi nhận hàng"},
                {"code": PaymentMethod.VNPAY.value, "label": "Thẻ ngân hàng"},
            ],
            "subtotal_raw": CheckoutService._money(subtotal_raw),
            "subtotal": CheckoutService._money(subtotal_raw),
            "shipping_total_raw": CheckoutService._money(shipping_total_raw),
            "shipping_total": CheckoutService._money(shipping_total_raw),
            "voucher_discount_total_raw": CheckoutService._money(voucher_discount_total_raw),
            "voucher_discount_total": CheckoutService._money(voucher_discount_total_raw),
            "discount_total_raw": CheckoutService._money(voucher_discount_total_raw),
            "discount_total": CheckoutService._money(voucher_discount_total_raw),
            "total_raw": CheckoutService._money(total_raw),
            "total": CheckoutService._money(total_raw),
            "item_count": sum(int(item["quantity"]) for item in state.get("items", [])),
            "shops": list(shops_map.values()),
        }

    @staticmethod
    def _normalize_state(user_id: int, payload: dict[str, Any] | None) -> dict[str, Any]:
        existing = CheckoutService._get_state() or {}
        input_payload = payload or {}
        items_payload = input_payload.get("items")
        if items_payload is None:
            items_payload = CheckoutService._cart_items_to_checkout_items()

        items: list[dict[str, int]] = []
        for item in items_payload:
            variant_id = item.get("variant_id")
            product_id = item.get("product_id")
            quantity = int(item.get("quantity", 1))
            if not variant_id or not product_id:
                raise ValidationError("Thiếu product_id hoặc variant_id")
            if quantity <= 0:
                raise ValidationError("Số lượng phải lớn hơn 0")
            variant = ProductVariant.query.get(int(variant_id))
            if not variant or int(variant.product_id) != int(product_id):
                raise ValidationError("Sản phẩm hoặc phân loại không hợp lệ")
            if quantity > int(variant.stock or 0):
                raise ValidationError("Số lượng vượt quá tồn kho")
            items.append(
                {
                    "product_id": int(product_id),
                    "variant_id": int(variant_id),
                    "quantity": quantity,
                }
            )

        if not items:
            raise ValidationError("Không có sản phẩm để checkout")

        addresses = UserService.get_addresses(user_id)
        default_address = next((item for item in addresses if item.get("is_default")), None)

        return {
            "items": items,
            "source": input_payload.get("source") or existing.get("source") or ("cart" if payload is None else "buy_now"),
            "payment_method": (input_payload.get("payment_method") or existing.get("payment_method") or PaymentMethod.COD.value),
            "shop_vouchers": dict(existing.get("shop_vouchers") or {}),
            "shipping_methods": dict(existing.get("shipping_methods") or {}),
            "address_id": input_payload.get("address_id") or existing.get("address_id") or (default_address or {}).get("id"),
        }

    @staticmethod
    def _cart_items_to_checkout_items() -> list[dict[str, int]]:
        cart = CartService.get_cart()
        items = []
        for item in cart.get("items", {}).values():
            items.append(
                {
                    "product_id": int(item.get("product_id")),
                    "variant_id": int(item.get("variant_id")),
                    "quantity": int(item.get("quantity", 1)),
                }
            )
        return items

    @staticmethod
    def _serialize_item(variant: ProductVariant, quantity: int) -> dict[str, Any]:
        pricing = CheckoutService._get_variant_pricing(variant)
        product = variant.product
        shop = product.shop if product else None
        item_total_raw = pricing["effective_price"] * quantity

        return {
            "product_id": int(product.id),
            "variant_id": int(variant.id),
            "product_name": product.name,
            "product_image": CartService._image_url(variant.image_url or product.thumbnail),
            "shop_id": int(shop.id) if shop else None,
            "shop_name": shop.name if shop else "OneShop",
            "size": CartService._variant_attr(variant, "size"),
            "color": CartService._variant_attr(variant, "color"),
            "variant_price_raw": CheckoutService._money(pricing["variant_price"]),
            "variant_price": CheckoutService._money(pricing["variant_price"]),
            "original_price_raw": CheckoutService._money(pricing["variant_price"]),
            "original_price": CheckoutService._money(pricing["variant_price"]),
            "flash_price_raw": CheckoutService._money(pricing["flash_price"]) if pricing["flash_price"] is not None else None,
            "flash_price": CheckoutService._money(pricing["flash_price"]) if pricing["flash_price"] is not None else None,
            "flash_discount_raw": CheckoutService._money(pricing["flash_discount"]),
            "flash_discount": CheckoutService._money(pricing["flash_discount"]),
            "promotion_discount_raw": CheckoutService._money(pricing["promotion_discount"]),
            "promotion_discount": CheckoutService._money(pricing["promotion_discount"]),
            "effective_price_raw": CheckoutService._money(pricing["effective_price"]),
            "effective_price": CheckoutService._money(pricing["effective_price"]),
            "quantity": quantity,
            "stock": int(variant.stock or 0),
            "item_total_raw": CheckoutService._money(item_total_raw),
            "item_total": CheckoutService._money(item_total_raw),
            "shipping_fees": {
                code: CheckoutService._money(getattr(variant, config["variant_fee"], 0) or 0)
                for code, config in CheckoutService.SHIPPING_METHODS.items()
            },
        }

    @staticmethod
    def _build_shipping_methods(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        methods = []
        if not items:
            return methods

        shop = Product.query.get(int(items[0]["product_id"])).shop
        for code, config in CheckoutService.SHIPPING_METHODS.items():
            if shop and not getattr(shop, config["shop_flag"], False):
                continue
            total_fee = Decimal("0")
            for item in items:
                variant = ProductVariant.query.get(int(item["variant_id"]))
                total_fee += Decimal(str(getattr(variant, config["variant_fee"], 0) or 0))
            methods.append(
                {
                    "code": code,
                    "label": config["label"],
                    "fee_raw": CheckoutService._money(total_fee),
                    "fee": CheckoutService._money(total_fee),
                    "selected": False,
                }
            )
        return methods

    @staticmethod
    def _resolve_variant(item_entry: dict[str, Any]) -> ProductVariant:
        variant = ProductVariant.query.get(int(item_entry["variant_id"]))
        if not variant or not variant.product:
            raise NotFoundError("Không tìm thấy phân loại sản phẩm")
        if int(variant.product_id) != int(item_entry["product_id"]):
            raise ValidationError("Phân loại sản phẩm không khớp")
        return variant

    @staticmethod
    def _get_variant_pricing(variant: ProductVariant) -> dict[str, Decimal | None]:
        base_price = Decimal(str(variant.price or 0))
        flash_sale = CheckoutService._get_active_flash_sale(variant.id)
        promotion = CheckoutService._get_active_promotion(variant.id)

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
    def _get_valid_voucher(*, shop_id: int, voucher_id: int | None = None, voucher_code: str | None = None) -> Voucher | None:
        now = datetime.now(timezone.utc)
        query = Voucher.query.filter(
            Voucher.shop_id == shop_id,
            Voucher.is_active.is_(True),
            Voucher.start_time <= now,
            Voucher.end_time >= now,
            Voucher.used_count < Voucher.usage_limit,
        )
        if voucher_id is not None:
            query = query.filter(Voucher.id == voucher_id)
        if voucher_code is not None:
            query = query.filter(Voucher.code == voucher_code.strip())
        return query.first()

    @staticmethod
    def _cleanup_after_confirm(state: dict[str, Any]) -> None:
        if state.get("source") == "cart":
            cart = CartService.get_cart()
            item_keys = {str(item["variant_id"]) for item in state.get("items", [])}
            for key in item_keys:
                cart.get("items", {}).pop(key, None)
            CartService._cleanup_applied_vouchers(cart)
            CartService._mark_session_dirty()
        session.pop(CheckoutService.SESSION_KEY, None)
        session.modified = True

    @staticmethod
    def _save_state(state: dict[str, Any]) -> None:
        session[CheckoutService.SESSION_KEY] = state
        session.modified = True

    @staticmethod
    def _get_state() -> dict[str, Any] | None:
        return session.get(CheckoutService.SESSION_KEY)

    @staticmethod
    def _require_state() -> dict[str, Any]:
        state = CheckoutService._get_state()
        if not state or not state.get("items"):
            raise ValidationError("Checkout chưa được khởi tạo")
        return state

    @staticmethod
    def _money(value: Decimal | int | float | str | None) -> float:
        return float(Decimal(str(value or 0)).quantize(Decimal("0.01")))