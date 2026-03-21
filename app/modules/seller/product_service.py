from dataclasses import dataclass
from decimal import Decimal
import re

from app.common.exceptions import ForbiddenError, NotFoundError, ValidationError, AppException
from app.core.enums.product_status import ProductStatus
from app.models import Product, ProductCategory
from .repository import SellerRepository
from app.extensions.db import db
from .dto import SellerProductCreateDTO
@dataclass
class SellerProductUpdateDTO:
    product_id: int
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    stock: int | None = None
    category_id: int | None = None


class SellerProductService:
    @staticmethod
    def _slugify(name: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
        return base or "product"

    @staticmethod
    def _validate_price(price: Decimal):
        if price <= 0:
            raise ValidationError("Giá sản phẩm phải lớn hơn 0")

    @staticmethod
    def _validate_stock(stock: int):
        if stock < 0:
            raise ValidationError("Tồn kho không được âm")

    @staticmethod
    def _check_ownership(product: Product, shop_id: int):
        if product.shop_id != shop_id:
            raise ForbiddenError("Bạn không có quyền thao tác sản phẩm này")

    # ================= CREATE PRODUCT =================

    @staticmethod
    def create(shop_id: int, dto: SellerProductCreateDTO):

        if not dto.name or len(dto.name.strip()) < 3:
            raise ValidationError("Tên sản phẩm tối thiểu 3 ký tự")

        slug_base = SellerProductService._slugify(dto.name)
        slug = slug_base
        idx = 1

        while Product.query.filter_by(slug=slug).first():
            idx += 1
            slug = f"{slug_base}-{idx}"

        product = Product(
            shop_id=shop_id,
            name=dto.name.strip(),
            slug=slug,
            description=dto.description,
            thumbnail=dto.images[0] if dto.images else None,
            status=ProductStatus.DRAFT,
        )

        SellerRepository.create_product(product)
 
        if dto.category_ids:
            for idx, cat_id in enumerate(dto.category_ids):
                db.session.add(ProductCategory(
                    product_id=product.id,
                    category_id=cat_id,
                    is_primary=(idx == 0)
                ))

        # tạo variants
        SellerRepository.create_product_variants(product.id, dto.variants)

        if dto.images:
            SellerRepository.create_product_images(product.id, dto.images)

        SellerRepository.commit()

        return {
            "id": product.id,
            "name": product.name,
            "status": product.status.value
        }

    # ================= LIST PRODUCTS =================

    @staticmethod
    def list_products(shop_id: int):

        products = SellerRepository.list_products(shop_id)

        result = []

        for p in products:

            variants = p.variants

            price = min(v.price for v in variants) if variants else 0
            stock = sum(v.stock for v in variants) if variants else 0

            result.append({
                "id": p.id,
                "name": p.name,
                "price": float(price),
                "stock": stock,
                "status": p.status.value,
            })

        return result

    # ================= UPDATE PRODUCT =================

    @staticmethod
    def update(shop_id: int, dto: SellerProductUpdateDTO):

        product = SellerRepository.get_product(shop_id, dto.product_id)

        if not product or product.status == ProductStatus.DELETED:
            raise NotFoundError("Không tìm thấy sản phẩm")

        SellerProductService._check_ownership(product, shop_id)

        if dto.name is not None:
            if len(dto.name.strip()) < 3:
                raise ValidationError("Tên sản phẩm tối thiểu 3 ký tự")
            product.name = dto.name.strip()

        if dto.description is not None:
            product.description = dto.description

        if dto.price is not None:
            SellerProductService._validate_price(dto.price)
            for v in product.variants:
                v.price = dto.price

        if dto.stock is not None:
            SellerProductService._validate_stock(dto.stock)

            for v in product.variants:
                v.stock = dto.stock

            if dto.stock == 0:
                product.status = ProductStatus.OUT_OF_STOCK
            elif product.status == ProductStatus.OUT_OF_STOCK:
                product.status = ProductStatus.ACTIVE

        if dto.category_id is not None:
            db.session.add(ProductCategory(
                product_id=product.id,
                category_id=dto.category_id,
                is_primary=True
            ))

        SellerRepository.commit()

        return {
            "id": product.id,
            "updated": True
        }

    # ================= UPDATE STOCK =================

    @staticmethod
    def update_stock(shop_id: int, product_id: int, stock: int):

        SellerProductService._validate_stock(stock)

        product = SellerRepository.get_product(shop_id, product_id)

        if not product or product.status == ProductStatus.DELETED:
            raise NotFoundError("Không tìm thấy sản phẩm")

        SellerProductService._check_ownership(product, shop_id)

        for v in product.variants:
            v.stock = stock

        if stock == 0:
            product.status = ProductStatus.OUT_OF_STOCK
        elif product.status == ProductStatus.OUT_OF_STOCK:
            product.status = ProductStatus.ACTIVE

        SellerRepository.commit()

        return {
            "id": product.id,
            "stock": product.stock_quantity
        }

    # ================= UPDATE STATUS =================

    @staticmethod
    def update_status(shop_id: int, product_id: int, status: str):

        allowed_status = {
            ProductStatus.ACTIVE.value,
            ProductStatus.HIDDEN.value,
            ProductStatus.DRAFT.value,
            ProductStatus.OUT_OF_STOCK.value,
            ProductStatus.DELETED.value,
        }

        if status not in allowed_status:
            raise ValidationError("Trạng thái không hợp lệ")

        product = SellerRepository.get_product(shop_id, product_id)

        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")

        SellerProductService._check_ownership(product, shop_id)

        # logic tồn kho
        total_stock = sum(v.stock for v in product.variants)

        if total_stock == 0 and status == ProductStatus.ACTIVE.value:
            status = ProductStatus.OUT_OF_STOCK.value

        elif total_stock > 0 and status == ProductStatus.OUT_OF_STOCK.value:
            status = ProductStatus.ACTIVE.value

        product.status = ProductStatus(status)

        SellerRepository.commit()

        return {
            "id": product.id,
            "status": product.status.value
        }
    # ================= SOFT DELETE =================

    @staticmethod
    def soft_delete(shop_id: int, product_id: int):

        product = SellerRepository.get_product(shop_id, product_id)

        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")

        SellerProductService._check_ownership(product, shop_id)

        product.status = ProductStatus.DELETED

        SellerRepository.commit()

        return {
            "id": product.id,
            "deleted": True
        }
    @staticmethod
    def restock(shop_id: int, product_id: int, quantity: int):

        if quantity <= 0:
            raise ValidationError("Số lượng nhập thêm phải > 0")

        product = SellerRepository.get_product(shop_id, product_id)

        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")

        SellerProductService._check_ownership(product, shop_id)

        for v in product.variants:
            v.stock += quantity

        total_stock = sum(v.stock for v in product.variants)

        if total_stock > 0 and product.status == ProductStatus.OUT_OF_STOCK:
            product.status = ProductStatus.ACTIVE

        SellerRepository.commit()

        return {
            "id": product.id,
            "stock_quantity": sum(v.stock for v in product.variants),
            "status": product.status.value
        }
    @staticmethod
    def update_variants(shop_id, product_id, name, description, variants):

        product = SellerRepository.get_product(shop_id, product_id)

        if not product:
            raise NotFoundError("Không tìm thấy sản phẩm")

        product.name = name
        product.description = description

        # xóa variant cũ
        SellerRepository.delete_variants(product_id)

        # tạo lại variant
        SellerRepository.create_product_variants(product_id, variants)

        SellerRepository.commit()
