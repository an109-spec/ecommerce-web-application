from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.common.exceptions import ValidationError


@dataclass
class ProductCreateDTO:
    name: str
    slug: str
    description: str | None
    price: Decimal
    stock_quantity: int
    category_ids: list[int] 
    thumbnail: str | None

    @staticmethod
    def from_dict(data: dict) -> "ProductCreateDTO":
        name = (data.get("name") or "").strip()
        slug = (data.get("slug") or "").strip().lower()
        if not name:
            raise ValidationError("name là bắt buộc")
        if not slug:
            raise ValidationError("slug là bắt buộc")

        try:
            price = Decimal(str(data.get("price")))
        except (InvalidOperation, TypeError):
            raise ValidationError("price không hợp lệ")
        if price < 0:
            raise ValidationError("price phải >= 0")

        try:
            stock_quantity = int(data.get("stock_quantity", 0))
        except (TypeError, ValueError):
            raise ValidationError("stock_quantity không hợp lệ")
        if stock_quantity < 0:
            raise ValidationError("stock_quantity phải >= 0")

        raw_category_ids = data.get("category_ids") or []

        if not isinstance(raw_category_ids, list):
            raise ValidationError("category_ids phải là list")

        category_ids = []
        for cid in raw_category_ids:
            try:
                category_ids.append(int(cid))
            except (TypeError, ValueError):
                raise ValidationError("category_ids chứa giá trị không hợp lệ")

        thumbnail = data.get("thumbnail")
        description = data.get("description")

        return ProductCreateDTO(
            name=name,
            slug=slug,
            description=description,
            price=price,
            stock_quantity=stock_quantity,
            category_ids=category_ids,
            thumbnail=thumbnail,
        )


@dataclass
class ProductUpdateDTO:
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    price: Decimal | None = None
    stock_quantity: int | None = None
    category_ids: list[int] | None = None
    category_ids_provided: bool = False
    thumbnail: str | None = None


    @staticmethod
    def from_dict(data: dict) -> "ProductUpdateDTO":
        dto = ProductUpdateDTO()

        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                raise ValidationError("name không được rỗng")
            dto.name = name

        if "slug" in data:
            slug = (data.get("slug") or "").strip().lower()
            if not slug:
                raise ValidationError("slug không được rỗng")
            dto.slug = slug

        if "price" in data:
            try:
                price = Decimal(str(data.get("price")))
            except (InvalidOperation, TypeError):
                raise ValidationError("price không hợp lệ")
            if price < 0:
                raise ValidationError("price phải >= 0")
            dto.price = price

        if "stock_quantity" in data:
            try:
                stock_quantity = int(data.get("stock_quantity"))
            except (TypeError, ValueError):
                raise ValidationError("stock_quantity không hợp lệ")
            if stock_quantity < 0:
                raise ValidationError("stock_quantity phải >= 0")
            dto.stock_quantity = stock_quantity

        if "category_ids" in data:
            raw = data.get("category_ids") or []
            if not isinstance(raw, list):
                raise ValidationError("category_ids phải là list")

            dto.category_ids = []
            for cid in raw:
                try:
                    dto.category_ids.append(int(cid))
                except (TypeError, ValueError):
                    raise ValidationError("category_ids không hợp lệ")

            dto.category_ids_provided = True

        if "description" in data:
            dto.description = data.get("description")

        if "thumbnail" in data:
            dto.thumbnail = data.get("thumbnail")

        return dto


@dataclass
class ProductResponseDTO:
    id: int
    name: str
    slug: str
    description: str | None
    price: str
    stock_quantity: int
    category_ids: list[int] 
    thumbnail: str | None
    created_at: str
    updated_at: str
    shop_id: int | None = None
    shop_name: str | None = None

    @staticmethod
    def from_model(product) -> "ProductResponseDTO":
        variants = product.variants
        price = min(v.price for v in variants) if variants else 0
        stock = sum(v.stock for v in variants) if variants else 0
        return ProductResponseDTO(
            id=product.id,
            name=product.name,
            slug=product.slug,
            description=product.description,
            price=str(price),
            stock_quantity=stock,
            category_ids=[pc.category_id for pc in product.product_categories],
            thumbnail=product.thumbnail,
            created_at=product.created_at.isoformat(),
            updated_at=product.updated_at.isoformat(),
            shop_id=product.shop_id,
            shop_name=product.shop.name if getattr(product, "shop", None) else None,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "category_ids": self.category_ids,
            "thumbnail": self.thumbnail,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
             "shop_id": self.shop_id,
            "shop_name": self.shop_name,
        }


@dataclass
class ReviewCreateDTO:
    user_id: int
    rating: int
    comment: str | None

    @staticmethod
    def from_dict(data: dict, fallback_user_id: int | None = None) -> "ReviewCreateDTO":
        raw_user_id = data.get("user_id", fallback_user_id)
        if raw_user_id is None:
            raise ValidationError("user_id là bắt buộc")
        try:
            user_id = int(raw_user_id)
        except (TypeError, ValueError):
            raise ValidationError("user_id không hợp lệ")

        try:
            rating = int(data.get("rating"))
        except (TypeError, ValueError):
            raise ValidationError("rating không hợp lệ")

        if rating < 1 or rating > 5:
            raise ValidationError("rating phải trong khoảng 1-5")

        comment = data.get("comment")
        if comment is not None:
            comment = str(comment).strip()

        return ReviewCreateDTO(user_id=user_id, rating=rating, comment=comment)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "rating": self.rating,
            "comment": self.comment,
        }