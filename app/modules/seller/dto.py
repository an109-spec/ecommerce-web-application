from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal

@dataclass
class SellerProductCreateDTO:
    name: str
    description: Optional[str]
    images: List[str]
    variants: list[dict]
    category_ids: list[int] | None = None
    
@dataclass
class CreateShopDTO:
    name: str
    pickup_address: str
    email: str
    phone: str


@dataclass
class ShippingSetupDTO:
    fast: bool
    same_day: bool
    express: bool
    self_delivery: bool
    pickup_point: bool
    bulky: bool

@dataclass
class CreateProductDTO:
    name: str
    price: float
    stock: int
    description: str | None = None
