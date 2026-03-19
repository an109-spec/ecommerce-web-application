# modules/order/routes.py

from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from app.common.exceptions import AppException
from app.modules.product.dto import ReviewCreateDTO
from app.modules.product.service import ProductService
from app.modules.seller.repository import SellerRepository
from .service import OrderService
from app.core.enums.order_status import OrderStatus
from .workflow import apply_transition

order_bp = Blueprint("order", __name__, url_prefix="/order")


# ================= USER =================

def require_login():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id


@order_bp.route("/")
def user_order_list():
    user_id = require_login()
    if not user_id:
        return redirect(url_for("auth.login"))

    status = (request.args.get("status") or "ALL").upper()
    orders = OrderService.get_user_orders(user_id, status)
    return render_template(
        "order/user/order_list.html",
        orders=orders,
        status=status,
        order_statuses=list(OrderStatus)
    )


@order_bp.route("/<int:order_id>")
def user_order_detail(order_id):
    user_id = require_login()
    if not user_id:
        return redirect(url_for("auth.login"))

    order = OrderService.get_order_detail(order_id, user_id)
    timeline = OrderService.build_timeline(order)
    customer = OrderService.get_customer_info(order)
    can_cancel = order.status in {OrderStatus.PENDING, OrderStatus.CONFIRMED}
    show_review_form = (
        order.status == OrderStatus.DELIVERED
        and not OrderService.has_review_by_user(order, user_id)
    )

    return render_template(
        "order/user/order_detail.html",
        order=order,
        timeline=timeline,
        customer=customer,
        can_cancel=can_cancel,
        show_review_form=show_review_form,
    )

@order_bp.route("/<int:order_id>/cancel", methods=["POST"])
def buyer_cancel_order(order_id):
    user_id = require_login()
    if not user_id:
        return redirect(url_for("auth.login"))
    try:
        OrderService.cancel_order(order_id, user_id, by="BUYER")
        flash("Hủy đơn thành công", "success")
    except AppException as exc:
        flash(str(exc), "error")
    return redirect(url_for("order.user_order_detail", order_id=order_id))


@order_bp.route("/<int:order_id>/review", methods=["POST"])
def buyer_submit_review(order_id):
    user_id = require_login()
    if not user_id:
        return redirect(url_for("auth.login"))
    try:
        order = OrderService.get_order_detail(order_id, user_id)
        if order.status != OrderStatus.DELIVERED:
            raise AppException("Chưa thể đánh giá đơn hàng", status_code=422)
        for item in order.items:
            rating = request.form.get(f"rating_{item.id}")
            if not rating:
                continue
            dto = ReviewCreateDTO.from_dict({
                "user_id": user_id,
                "rating": rating,
                "comment": request.form.get(f"comment_{item.id}", ""),
                "order_id": order.id,
                "order_item_id": item.id,
            })
            ProductService.add_review(item.product_id, user_id, dto)
        flash("Gửi đánh giá thành công", "success")
    except AppException as exc:
        flash(str(exc), "error")
    return redirect(url_for("order.user_order_detail", order_id=order_id))


@order_bp.route("/seller/<int:order_id>")
def seller_order_detail(order_id):
    user_id = require_login()
    if not user_id:
        return redirect(url_for("auth.login"))
    shop = SellerRepository.get_shop_by_owner_id(user_id)
    if not shop:
        return redirect(url_for("auth.login"))
    order = OrderService.get_order_detail_for_seller(order_id, shop.id)
    timeline = OrderService.build_timeline(order)
    customer = OrderService.get_customer_info(order)
    return render_template("seller/order/order_detail.html", order=order, timeline=timeline, customer=customer)


@order_bp.route("/seller/<int:order_id>/action", methods=["POST"])
def seller_order_action(order_id):
    user_id = require_login()
    if not user_id:
        return redirect(url_for("auth.login"))
    shop = SellerRepository.get_shop_by_owner_id(user_id)
    if not shop:
        return redirect(url_for("auth.login"))

    action = (request.form.get("action") or "").upper()
    order = OrderService.get_order_detail_for_seller(order_id, shop.id)
    action_map = {
        "CONFIRM": OrderStatus.CONFIRMED,
        "START_PREPARING": OrderStatus.PREPARING,
        "READY_TO_SHIP": OrderStatus.SHIPPING,
        "MARK_DELIVERED": OrderStatus.DELIVERED,
    }
    try:
        if action == "CANCEL":
            OrderService.cancel_order(order_id, user_id, by="SELLER")
        elif action in action_map:
            apply_transition(order, action_map[action])
        else:
            raise AppException("Hành động không hợp lệ", status_code=422)
        flash("Cập nhật đơn hàng thành công", "success")
    except AppException as exc:
        flash(str(exc), "error")
    return redirect(url_for("order.seller_order_detail", order_id=order_id))


@order_bp.route("/tracking/<order_code>")
def tracking(order_code):
    data = OrderService.track_by_order_code(order_code)
    return render_template(
        "order/user/tracking.html",
        tracking=data
    )


# ================= ADMIN =================

@order_bp.route("/admin")
def admin_order_list():
    user_id = require_login()
    if not user_id:
        return redirect(url_for("auth.login"))

    # Nếu có role admin thì check thêm ở đây
    orders = OrderService.get_all_orders()
    return render_template(
        "order/admin/admin_order_list.html",
        orders=orders
    )


@order_bp.route("/admin/<int:order_id>")
def admin_order_detail(order_id):
    user_id = require_login()
    if not user_id:
        return redirect(url_for("auth.login"))

    order = OrderService.get_order_detail_admin(order_id)
    timeline = OrderService.build_timeline(order)

    return render_template(
        "order/admin/admin_order_detail.html",
        order=order,
        timeline=timeline
    )


@order_bp.route("/admin/<int:order_id>/update", methods=["POST"])
def admin_update_status(order_id):
    user_id = require_login()
    if not user_id:
        return redirect(url_for("auth.login"))

    new_status = request.form.get("status")
    OrderService.update_status(order_id, new_status)

    return redirect(url_for("order.admin_order_detail", order_id=order_id))