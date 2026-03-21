from app.common.exceptions import ValidationError, AppException
from app.extensions.db import db
from app.models.order import OrderTracking
from app.core.enums.order_status import OrderStatus
from datetime import datetime, timezone

VALID_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
    OrderStatus.PREPARING: [OrderStatus.SHIPPING],
    OrderStatus.SHIPPING: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}


def validate_transition(old_status: OrderStatus, new_status: OrderStatus):
    allowed = VALID_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise ValidationError(
            f"Không thể chuyển trạng thái từ {old_status} sang {new_status}"
        )


# Trong OrderService hoặc logic xử lý transition
@staticmethod
def apply_transition(order, next_status):
    # Định nghĩa các bước đi hợp lệ
    valid_transitions = {
        OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
        OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
        OrderStatus.PREPARING: [OrderStatus.SHIPPING, OrderStatus.CANCELLED],
        OrderStatus.SHIPPING: [OrderStatus.DELIVERED],
    }

    current = order.status
    if next_status not in valid_transitions.get(current, []):
        raise AppException(f"Không thể chuyển trạng thái từ {current.value} sang {next_status.value}")

    order.status = next_status
    
    # Cập nhật timestamp tương ứng
    now = datetime.now(timezone.utc)
    if next_status == OrderStatus.CONFIRMED: order.confirmed_at = now
    elif next_status == OrderStatus.PREPARING: order.preparing_at = now
    elif next_status == OrderStatus.SHIPPING: order.shipping_at = now
    elif next_status == OrderStatus.DELIVERED: order.delivered_at = now
    
    db.session.commit()


def build_timeline(order):
    history = (
        OrderTracking.query
        .filter_by(order_id=order.id)
        .order_by(OrderTracking.created_at.asc())
        .all()
    )

    return [
        {
            "status": item.status,
            "created_at": item.created_at.isoformat()
        }
        for item in history
    ]