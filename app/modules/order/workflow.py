from app.common.exceptions import ValidationError
from app.extensions.db import db
from app.models.order import OrderTracking
from .status import OrderStatus
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


def apply_transition(order, new_status: OrderStatus):
    validate_transition(order.status, new_status)

    order.status = new_status
    now = datetime.now(timezone.utc)
    if new_status == OrderStatus.CONFIRMED:
        order.confirmed_at = order.confirmed_at or now
    if new_status == OrderStatus.PREPARING:
        order.preparing_at = order.preparing_at or now
    if new_status == OrderStatus.SHIPPING:
        order.shipping_at = order.shipping_at or now
    if new_status == OrderStatus.DELIVERED:
        order.delivered_at = order.delivered_at or now
    tracking = OrderTracking(
        order_id=order.id,
        status=new_status
    )

    db.session.add(tracking)
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