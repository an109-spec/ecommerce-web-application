from app.common.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions.db import db

from app.models import Product

def _validate_quantity(quantity: int) -> int:
    try:
        parsed = int(quantity)
    except (TypeError, ValueError):
        raise ValidationError("quantity không hợp lệ")
    if parsed <= 0:
        raise ValidationError("quantity phải > 0")
    return parsed


def check_stock(product_id: int, quantity: int) -> bool:
    qty = _validate_quantity(quantity)
    product = Product.query.get(product_id)
    if not product:
        raise NotFoundError("Không tìm thấy sản phẩm")
    return product.stock_quantity >= qty


def decrease_stock(product_id: int, quantity: int) -> int:
    qty = _validate_quantity(quantity)
    product = Product.query.get(product_id)
    if not product:
        raise NotFoundError("Không tìm thấy sản phẩm")

    if product.stock_quantity < qty:
        raise ConflictError("Không đủ hàng trong kho")

    product.stock_quantity -= qty
    if product.stock_quantity < 0:
        raise ConflictError("Stock không được âm")

    db.session.commit()
    return product.stock_quantity


def increase_stock(product_id: int, quantity: int) -> int:
    qty = _validate_quantity(quantity)
    product = Product.query.get(product_id)
    if not product:
        raise NotFoundError("Không tìm thấy sản phẩm")

    product.stock_quantity += qty
    if product.stock_quantity < 0:
        raise ConflictError("Stock không được âm")

    db.session.commit()
    return product.stock_quantity