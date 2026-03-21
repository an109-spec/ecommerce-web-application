from datetime import datetime, timezone
from app.extensions.db import db
from flask import jsonify
from app.models.promotion import Promotion
from app.models.flash_sale import FlashSale
from app.models.voucher import Voucher
from app.models.product import ProductVariant

class PromotionService:

    @staticmethod
    def create_promotion(name, variant_id, discount_percent, start_time, end_time):

        variant = ProductVariant.query.get(variant_id)

        if not variant:
            raise Exception("Variant không tồn tại")

        # ===== VALIDATE DISCOUNT =====
        if discount_percent <= 0 or discount_percent > 90:
            raise Exception("Discount không hợp lệ")

        # ===== VALIDATE TIME =====
        if start_time >= end_time:
            raise Exception("Thời gian khuyến mãi không hợp lệ")

        promo = Promotion(
            name=name,
            variant_id=variant_id,
            discount_percent=discount_percent,
            start_time=start_time,
            end_time=end_time,
        )

        db.session.add(promo)
        db.session.commit()

        return promo

    @staticmethod
    def delete_promotion(promo_id):

        promo = Promotion.query.get(promo_id)

        if not promo:
            return

        db.session.delete(promo)
        db.session.commit()

    @staticmethod
    def list_promotions(shop_id):

        from app.models.product import Product

        return (
            Promotion.query
            .join(ProductVariant, Promotion.variant_id == ProductVariant.id)
            .join(Product, ProductVariant.product_id == Product.id)
            .filter(Product.shop_id == shop_id)
            .all()
        )
    @staticmethod
    def get_active_promotions():

        now = datetime.now(timezone.utc)

        return Promotion.query.filter(
            Promotion.start_time <= now,
            Promotion.end_time >= now,
            Promotion.is_active == True
        ).all()
    @staticmethod
    def get_promotion(promo_id):

        promo = Promotion.query.get(promo_id)

        if not promo:
            raise Exception("Promotion không tồn tại")

        return promo
    @staticmethod
    def update_promotion(promo_id, name, discount_percent, start_time, end_time):

        promo = Promotion.query.get(promo_id)

        if not promo:
            raise Exception("Promotion không tồn tại")

        # ===== VALIDATE =====
        if discount_percent <= 0 or discount_percent > 90:
            raise Exception("Discount không hợp lệ")

        if start_time >= end_time:
            raise Exception("Thời gian không hợp lệ")

        promo.name = name
        promo.discount_percent = discount_percent
        promo.start_time = start_time
        promo.end_time = end_time

        db.session.commit()

        return promo
class VoucherService:

    @staticmethod
    def list_vouchers(shop_id):
        return Voucher.query.filter_by(shop_id=shop_id).all()


    @staticmethod
    def create_voucher(
        shop_id,
        name,
        code,
        discount_type,
        discount_value,
        min_order_value,
        usage_limit,
        start_time,
        end_time
    ):

        # tránh trùng code
        exists = Voucher.query.filter_by(code=code).first()
        if exists:
            raise Exception("Voucher code đã tồn tại")
        if start_time >= end_time:
            raise Exception("Thời gian voucher không hợp lệ")

        if discount_type == "percent":
            if discount_value <= 0 or discount_value > 90:
                raise Exception("Percent không hợp lệ")

        if discount_value <= 0:
            raise Exception("Discount phải > 0")

        voucher = Voucher(
            shop_id=shop_id,
            name=name,
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            min_order_value=min_order_value,
            usage_limit=usage_limit,
            used_count=0,
            start_time=start_time,
            end_time=end_time,
            is_active=True
        )

        db.session.add(voucher)
        db.session.commit()

        return voucher


    @staticmethod
    def update_voucher(
        voucher_id,
        name,
        code,
        discount_type,
        discount_value,
        min_order_value,
        usage_limit,
        start_time,
        end_time
    ):

        voucher = Voucher.query.get(voucher_id)

        if not voucher:
            raise Exception("Voucher không tồn tại")

        voucher.name = name
        voucher.code = code
        voucher.discount_type = discount_type
        voucher.discount_value = discount_value
        voucher.min_order_value = min_order_value
        voucher.usage_limit = usage_limit
        voucher.start_time = start_time
        voucher.end_time = end_time

        db.session.commit()

        return voucher


    @staticmethod
    def delete_voucher(voucher_id):

        voucher = Voucher.query.get(voucher_id)

        if not voucher:
            return

        db.session.delete(voucher)
        db.session.commit()


    @staticmethod
    def toggle_voucher(voucher_id):

        voucher = Voucher.query.get(voucher_id)

        if not voucher:
            return

        voucher.is_active = not voucher.is_active

        db.session.commit()


    @staticmethod
    def validate_voucher(code):

        now = datetime.now(timezone.utc)

        voucher = Voucher.query.filter_by(code=code).first()

        if not voucher:
            return None

        if not voucher.is_active:
            return None

        if voucher.used_count >= voucher.usage_limit:
            return None

        if voucher.start_time > now:
            return None

        if voucher.end_time < now:
            return None

        return voucher
    
    @staticmethod
    def list_public_active_vouchers():
        """Lấy danh sách tất cả voucher đang hoạt động cho người mua hiển thị ở Kho Voucher"""
        now = datetime.now(timezone.utc)
        return Voucher.query.filter(
            Voucher.is_active == True,
            Voucher.end_time >= now
        ).order_by(Voucher.end_time.asc()).all()
    
class FlashSaleService:
    @staticmethod
    def increase_sold(variant_id, quantity):
        from app.utils.time import utcnow
        now=utcnow()
        sale = FlashSale.query.filter(
        FlashSale.variant_id == variant_id,
        FlashSale.is_active == True,
        FlashSale.start_time <= now,
        FlashSale.end_time >= now
        ).first()

        if not sale:
            return
        # kiểm tra stock flash sale
        if sale.sold_count + quantity > sale.stock_limit:
            raise Exception("Flash sale sold out")


        sale.sold_count += quantity

        db.session.commit()
    # =========================
    # FLASH SALE
    # =========================
    @staticmethod
    def create_flash_sale(
        variant_id,
        discount_percent,
        stock_limit,
        start_time,
        end_time
    ):
        variant_id = int(variant_id)
        discount_percent = int(discount_percent)
        stock_limit = int(stock_limit)

        now = datetime.now(timezone.utc)
        if start_time >= end_time:
            raise Exception("Thời gian khuyến mãi không hợp lệ")
        if end_time <= now:
            raise Exception("Thời gian kết thúc phải lớn hơn hiện tại")

        # 1. kiểm tra variant tồn tại
        variant = ProductVariant.query.get(variant_id)
        if not variant:
            raise Exception("Variant không tồn tại")

        # 2. kiểm tra stock khả dụng theo khung thời gian tạo mới
        reserved_overlap = (
            db.session.query(db.func.coalesce(db.func.sum(FlashSale.stock_limit - FlashSale.sold_count), 0))
            .filter(
                FlashSale.variant_id == variant_id,
                FlashSale.is_active == True,
                FlashSale.end_time >= start_time,
                FlashSale.start_time <= end_time,
            )
            .scalar()
        )

        available_stock = max(variant.stock - int(reserved_overlap or 0), 0)

        if stock_limit <= 0 or stock_limit > available_stock:
            raise Exception(
                f"Flash sale vượt tồn kho của variant: {variant_id} (khả dụng: {available_stock})"
            )

        # 3. kiểm tra discount hợp lệ
        if discount_percent <= 0 or discount_percent > 90:
            raise Exception("Discount percent không hợp lệ")

        # 5. tạo flash sale
        sale = FlashSale(
            variant_id=variant_id,
            discount_percent=discount_percent,
            stock_limit=stock_limit,
            sold_count=0,
            start_time=start_time,
            end_time=end_time,
            is_active=True
        )

        db.session.add(sale)
        db.session.commit()

        return sale


    @staticmethod
    def list_flash_sales(shop_id):

        return (
            FlashSale.query
            .join(ProductVariant)
            .join(ProductVariant.product)
            .filter_by(shop_id=shop_id)
            .all()
        )
    @staticmethod
    def get_active_flash_sales():

        return FlashSale.query.filter(
            FlashSale.is_active == True,
            FlashSale.start_time <= datetime.now(timezone.utc),
            FlashSale.end_time >= datetime.now(timezone.utc)
        ).all()
    
    @staticmethod
    def update_flash_sale(
        flash_id,
        discount_percent,
        stock_limit,
        start_time,
        end_time
    ):

        discount_percent = int(discount_percent)
        stock_limit = int(stock_limit)

        sale = FlashSale.query.get(flash_id)

        if not sale:
            raise Exception("Flash sale không tồn tại")

        if start_time >= end_time:
            raise Exception("Thời gian flash sale không hợp lệ")

        if discount_percent <= 0 or discount_percent > 90:
            raise Exception("Discount không hợp lệ")

        variant = ProductVariant.query.get(sale.variant_id)

        if not variant:
            raise Exception("Variant không tồn tại")

        if stock_limit < sale.sold_count:
            raise Exception("Stock limit nhỏ hơn số đã bán")

        reserved_overlap = (
            db.session.query(
                db.func.coalesce(
                    db.func.sum(FlashSale.stock_limit - FlashSale.sold_count), 0
                )
            )
            .filter(
                FlashSale.variant_id == sale.variant_id,
                FlashSale.id != sale.id,
                FlashSale.is_active == True,
                FlashSale.end_time >= start_time,
                FlashSale.start_time <= end_time,
            )
            .scalar()
        )

        available_stock = max(variant.stock - int(reserved_overlap or 0), 0)

        if stock_limit > available_stock:
            raise Exception(
                f"Stock limit vượt tồn kho khả dụng ({available_stock})"
            )

        sale.discount_percent = discount_percent
        sale.stock_limit = stock_limit
        sale.start_time = start_time
        sale.end_time = end_time

        db.session.commit()

        return sale