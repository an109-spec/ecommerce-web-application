from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    SHIPPING = "shipping"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

    @classmethod
    def from_input(cls, raw_status: str) -> "OrderStatus":
        normalized = (raw_status or "").strip()
        if not normalized:
            raise ValueError("Empty order status")
        # Ưu tiên parse theo enum name (PENDING/CONFIRMED/...)
        try:
            return cls[normalized.upper()]
        except KeyError:
            # Fallback cho dữ liệu đã ở dạng value (pending/confirmed/...)
            return cls(normalized.lower())


class PaymentMethod(str, Enum):
    COD = "COD"
    VNPAY = "VNPAY"