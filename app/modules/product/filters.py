from decimal import Decimal, InvalidOperation

from app.common.exceptions import ValidationError

from app.models.product import Product,ProductCategory, ProductVariant
from app.models.review import Review

def _parse_decimal(name: str, raw_value):
    if raw_value in (None, ""):
        return None
    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"{name} không hợp lệ")
    return value


def filter_by_price(query, min_price=None, max_price=None):
    parsed_min = _parse_decimal("min_price", min_price)
    parsed_max = _parse_decimal("max_price", max_price)

    if parsed_min is None and parsed_max is None:
        return query

    query = query.join(ProductVariant)

    if parsed_min is not None:
        query = query.filter(ProductVariant.price >= parsed_min)

    if parsed_max is not None:
        query = query.filter(ProductVariant.price <= parsed_max)

    if parsed_min is not None and parsed_max is not None and parsed_min > parsed_max:
        raise ValidationError("min_price không được lớn hơn max_price")

    return query


def filter_by_category(query, category_id=None):
    if category_id in (None, ""):
        return query

    try:
        parsed_category = int(category_id)
    except (TypeError, ValueError):
        raise ValidationError("category không hợp lệ")

    return query.join(ProductCategory).filter(
        ProductCategory.category_id == parsed_category
    )


def sort_products(query, sort_type=None):
    sort_type = (sort_type or "newest").strip()

    from app.models.product import ProductVariant

    if sort_type == "price_asc":
        return query.join(ProductVariant).order_by(ProductVariant.price.asc())

    if sort_type == "price_desc":
        return query.join(ProductVariant).order_by(ProductVariant.price.desc())

    if sort_type == "newest":
        return query.order_by(Product.created_at.desc(), Product.id.desc())

    raise ValidationError("sort không hợp lệ")