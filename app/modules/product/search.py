from sqlalchemy import or_
from app.models.product import Product
from app.models.shop import Shop

def search_products(query, keyword: str | None):
    if not keyword:
        return query
    
    like_keyword = f"%{keyword.strip()}%"

    return query.outerjoin(Shop, Product.shop_id == Shop.id).filter(
        or_(
            Product.name.ilike(like_keyword),
            Product.description.ilike(like_keyword),
            Shop.name.ilike(like_keyword)
        )
    ).distinct()