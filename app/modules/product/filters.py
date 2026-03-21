from decimal import Decimal, InvalidOperation
from sqlalchemy import and_, func
from app.common.exceptions import ValidationError
from app.models.product import Product, ProductCategory, ProductVariant

def _parse_decimal(name: str, raw_value):
    if raw_value in (None, ""):
        return None
    try:
        return Decimal(str(raw_value))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"{name} không hợp lệ")

def filter_by_price(query, min_price=None, max_price=None):
    parsed_min = _parse_decimal("min_price", min_price)
    parsed_max = _parse_decimal("max_price", max_price)

    if parsed_min is None and parsed_max is None:
        return query

    # Sử dụng distinct() để tránh nhân bản dòng khi join với Variant
    query = query.join(ProductVariant).distinct()

    if parsed_min is not None:
        query = query.filter(ProductVariant.price >= parsed_min)
    if parsed_max is not None:
        query = query.filter(ProductVariant.price <= parsed_max)
    
    if parsed_min and parsed_max and parsed_min > parsed_max:
        raise ValidationError("Giá tối thiểu không được lớn hơn giá tối đa")

    return query

def filter_by_category(query, category_ids=None):
    """
    Cải tiến: category_ids có thể là một số ID đơn lẻ hoặc một danh sách ID
    """
    if not category_ids:
        return query

    # Chuyển đổi về list nếu đầu vào là string hoặc int đơn lẻ
    if isinstance(category_ids, (str, int)):
        category_ids = [category_ids]
    
    try:
        parsed_ids = [int(cid) for cid in category_ids if cid]
    except (TypeError, ValueError):
        raise ValidationError("Danh mục không hợp lệ")

    if not parsed_ids:
        return query

    # Sử dụng .in_() để lọc nhiều danh mục cùng lúc
    return query.join(ProductCategory).filter(
        ProductCategory.category_id.in_(parsed_ids)
    ).distinct()

def sort_products(query, sort_type=None):
    sort_type = (sort_type or "newest").strip()

    # Thêm sắp xếp theo lượt bán (sold_desc) để phục vụ mục Gợi ý sản phẩm
    if sort_type == "sold_desc":
        # Giả sử bạn có trường sold_count trong bảng Product hoặc ProductVariant
        # Nếu chưa có, ta tạm sắp xếp theo ID mới nhất hoặc thay bằng logic bán chạy của bạn
        return query.order_by(Product.id.desc()) 

    if sort_type == "price_asc":
        return query.join(ProductVariant).order_by(ProductVariant.price.asc()).distinct()

    if sort_type == "price_desc":
        return query.join(ProductVariant).order_by(ProductVariant.price.desc()).distinct()

    if sort_type == "newest":
        return query.order_by(Product.created_at.desc(), Product.id.desc())

    return query # Mặc định trả về query nếu không khớp

from sqlalchemy import or_, exists

def apply_filters(query, keyword=None, category_ids=None, min_price=None, max_price=None, freeship=None):

    if keyword and str(keyword).strip() and str(keyword).lower() != 'none':
        k = f"%{keyword.strip()}%"
        query = query.filter(Product.name.ilike(k))

    if category_ids:
        valid_ids = [int(cid) for cid in category_ids if str(cid).isdigit()]
        if valid_ids:
            query = query.join(ProductCategory).filter(ProductCategory.category_id.in_(valid_ids))

    is_fs_requested = str(freeship).lower() in ('1', 'true')

    if is_fs_requested:

        fs_condition = exists().where(ProductVariant.product_id == Product.id).where(
            and_(
                or_(ProductVariant.shipping_fast_fee == 0, ProductVariant.shipping_fast_fee.is_(None)),
                or_(ProductVariant.shipping_same_day_fee == 0, ProductVariant.shipping_same_day_fee.is_(None)),
                or_(ProductVariant.shipping_express_fee == 0, ProductVariant.shipping_express_fee.is_(None)),
                or_(ProductVariant.shipping_pickup_fee == 0, ProductVariant.shipping_pickup_fee.is_(None)),
                or_(ProductVariant.shipping_bulky_fee == 0, ProductVariant.shipping_bulky_fee.is_(None))
            )
        )
        query = query.filter(fs_condition)
    # 3. Lọc theo giá (nếu có)
    # Lưu ý: Khi lọc giá, ta phải join với Variant để kiểm tra cột price
    if min_price or max_price:
        # Dùng distinct() vì một sản phẩm có nhiều variant thỏa mãn khoảng giá
        query = query.join(ProductVariant).distinct()
        
        parsed_min = _parse_decimal("min_price", min_price)
        parsed_max = _parse_decimal("max_price", max_price)
        
        if parsed_min is not None:
            query = query.filter(ProductVariant.price >= parsed_min)
        if parsed_max is not None:
            query = query.filter(ProductVariant.price <= parsed_max)

    return query.distinct()