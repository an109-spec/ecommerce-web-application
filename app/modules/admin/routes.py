from datetime import datetime, timezone

from flask import flash, redirect, render_template, request, session, url_for
from sqlalchemy import func
from . import admin_bp
from app.common.security.permission import admin_required
from app.extensions.db import db
from app.models import AuditLog, FlashSale, Notification, Order, Product, ProductVariant, Shop, User
from app.core.enums.product_status import ProductStatus


def _current_admin() -> User:
    return User.query.get(session.get("user_id"))


def _log(action: str, target: str):
    admin = _current_admin()
    db.session.add(AuditLog(user_id=admin.id if admin else None, action=action, target=target))


def _notify(user_id: int, title: str, message: str):
    db.session.add(Notification(user_id=user_id, title=title, message=message, is_read=False))


@admin_bp.route("")
@admin_required
def root():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/dashboard")
@admin_required
def dashboard():

    total_users = User.query.count()
    total_shops = Shop.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()

    now = datetime.now(timezone.utc)
    running_flash_sales = FlashSale.query.filter(
        FlashSale.is_active.is_(True),
        FlashSale.start_time <= now,
        FlashSale.end_time >= now,
    ).count()

    return render_template(
        "admin/dashboard.html",
        stats={
            "total_users": total_users,
            "total_shops": total_shops,
            "total_products": total_products,
            "total_orders": total_orders,
            "running_flash_sales": running_flash_sales,
        },
    )


@admin_bp.route("/users")
@admin_required
def users():
    status_filter = (request.args.get("status") or "ALL").upper()
    query = User.query.order_by(User.created_at.desc())

    if status_filter == "BANNED":
        query = query.filter(User.is_banned.is_(True))
    elif status_filter == "ACTIVE":
        query = query.filter(User.is_banned.is_(False))

    return render_template("admin/users.html", users=query.all(), status_filter=status_filter)


@admin_bp.route("/users/<int:user_id>")
@admin_required
def user_detail(user_id: int):
    user = User.query.get_or_404(user_id)
    orders_count = Order.query.filter_by(user_id=user.id).count()
    return render_template("admin/user_detail.html", user=user, orders_count=orders_count, shop=user.shop)


@admin_bp.route("/users/<int:user_id>/ban", methods=["POST"])
@admin_required
def ban_user(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Không thể khóa tài khoản admin", "warning")
        return redirect(url_for("admin.users"))

    user.is_banned = True
    _log("BAN_USER", f"user_{user.id}")
    _notify(user.id, "Tài khoản bị khóa", "Tài khoản của bạn đã bị khóa. Liên hệ admin để được hỗ trợ.")
    db.session.commit()
    flash("Đã khóa tài khoản người dùng", "success")
    return redirect(url_for("admin.users"))

@admin_bp.route("/users/<int:user_id>/unban", methods=["POST"])
@admin_required
def unban_user(user_id: int):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    _log("UNBAN_USER", f"user_{user.id}")
    _notify(user.id, "Tài khoản đã mở khóa", "Tài khoản của bạn đã được mở khóa. Bạn có thể đăng nhập bình thường.")
    db.session.commit()
    flash("Đã mở khóa tài khoản", "success")
    return redirect(url_for("admin.users"))

@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Không thể xóa admin", "warning")
        return redirect(url_for("admin.users"))

    _log("DELETE_USER", f"user_{user.id}")
    db.session.delete(user)
    db.session.commit()
    flash("Đã xóa user", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/shops")
@admin_required
def shops():
    status_filter = (request.args.get("status") or "ALL").upper()
    query = Shop.query.order_by(Shop.created_at.desc())

    if status_filter in {"PENDING", "ACTIVE", "BANNED"}:
        query = query.filter(Shop.status == status_filter)

    return render_template("admin/shops.html", shops=query.all(), status_filter=status_filter)


@admin_bp.route("/shops/<int:shop_id>")
@admin_required
def shop_detail(shop_id: int):
    shop = Shop.query.get_or_404(shop_id)
    products_count = Product.query.filter_by(shop_id=shop.id).count()
    return render_template("admin/shop_detail.html", shop=shop, products_count=products_count)


@admin_bp.route("/shops/<int:shop_id>/approve", methods=["POST"])
@admin_required
def approve_shop(shop_id: int):
    shop = Shop.query.get_or_404(shop_id)
    shop.status = "ACTIVE"
    _log("APPROVE_SHOP", f"shop_{shop.id}")
    _notify(shop.owner_id, "Shop Approved", "Shop của bạn đã được duyệt và có thể bán hàng")
    db.session.commit()
    flash("Đã duyệt shop", "success")
    return redirect(url_for("admin.shops"))


@admin_bp.route("/shops/<int:shop_id>/ban", methods=["POST"])
@admin_required
def ban_shop(shop_id: int):
    shop = Shop.query.get_or_404(shop_id)
    shop.status = "BANNED"
    _log("BAN_SHOP", f"shop_{shop.id}")
    _notify(shop.owner_id, "Shop bị khóa", "Shop của bạn đã bị khóa. Lý do: Vi phạm chính sách")
    db.session.commit()
    flash("Đã khóa shop", "success")
    return redirect(url_for("admin.shops"))


@admin_bp.route("/shops/<int:shop_id>/unban", methods=["POST"])
@admin_required
def unban_shop(shop_id: int):
    shop = Shop.query.get_or_404(shop_id)
    shop.status = "ACTIVE"
    _log("UNBAN_SHOP", f"shop_{shop.id}")
    _notify(shop.owner_id, "Shop đã mở khóa", "Shop của bạn đã được mở khóa. Bạn có thể tiếp tục bán hàng")
    db.session.commit()
    flash("Đã mở khóa shop", "success")
    return redirect(url_for("admin.shops"))


@admin_bp.route("/shops/<int:shop_id>/delete", methods=["POST"])
@admin_required
def delete_shop(shop_id: int):
    shop = Shop.query.get_or_404(shop_id)
    owner = shop.owner

    _notify(shop.owner_id, "Shop đã bị xóa", "Shop của bạn đã bị xóa khỏi hệ thống. Hãy tạo shop mới để tiếp tục bán hàng")
    _log("DELETE_SHOP", f"shop_{shop.id}")

    Product.query.filter_by(shop_id=shop.id).delete(synchronize_session=False)
    db.session.delete(shop)

    if owner:
        owner.role = "user"
        owner.is_seller = False

    db.session.commit()
    flash("Đã xóa shop", "success")
    return redirect(url_for("admin.shops"))

@admin_bp.route("/products")
@admin_required
def products():
    status_filter = (request.args.get("status") or "ALL").upper()
    query = Product.query.order_by(Product.created_at.desc())

    status_map = {"PENDING": ProductStatus.DRAFT, "ACTIVE": ProductStatus.ACTIVE, "REJECTED": ProductStatus.HIDDEN}
    if status_filter in status_map:
        query = query.filter(Product.status == status_map[status_filter])

    return render_template("admin/products.html", products=query.all(), status_filter=status_filter)


@admin_bp.route("/products/<int:product_id>")
@admin_required
def product_detail(product_id: int):
    product = Product.query.get_or_404(product_id)
    return render_template("admin/product_detail.html", product=product)

@admin_bp.route("/products/<int:product_id>/approve", methods=["POST"])
@admin_required
def approve_product(product_id: int):
    product = Product.query.get_or_404(product_id)
    product.status = ProductStatus.ACTIVE
    _log("APPROVE_PRODUCT", f"product_{product.id}")
    if product.shop:
        _notify(product.shop.owner_id, "Product Approved", f'Sản phẩm "{product.name}" đã được duyệt và hiển thị')
    db.session.commit()
    flash("Đã duyệt sản phẩm", "success")
    return redirect(url_for("admin.products"))

@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def reject_product(product_id: int):
    product = Product.query.get_or_404(product_id)
    product.status = ProductStatus.HIDDEN
    _log("DELETE_PRODUCT", f"product_{product.id}")
    if product.shop:
        _notify(product.shop.owner_id, "Sản phẩm đã bị gỡ", f'Sản phẩm "{product.name}" đã bị gỡ do vi phạm chính sách')
    db.session.commit()
    flash("Đã gỡ sản phẩm", "success")
    return redirect(url_for("admin.products"))

@admin_bp.route("/flash-sales")
@admin_required
def flash_sales():
    sales = FlashSale.query.order_by(FlashSale.created_at.desc()).all()
    return render_template("admin/flash_sales.html", sales=sales)

@admin_bp.route("/flash-sales/<int:sale_id>/disable", methods=["POST"])
@admin_required
def disable_flash_sale(sale_id: int):
    sale = FlashSale.query.get_or_404(sale_id)
    sale.is_active = False
    sale.disabled_reason = "Giá không hợp lệ / vi phạm chính sách"
    _log("DISABLE_FLASH_SALE", f"flash_sale_{sale.id}")


    owner_id = None
    if sale.variant and sale.variant.product and sale.variant.product.shop:
        owner_id = sale.variant.product.shop.owner_id

    if owner_id:
        _notify(owner_id, "Flash sale bị tắt", "Flash sale của bạn đã bị tắt bởi Admin. Lý do: Giá không hợp lệ")

    db.session.commit()
    flash("Đã tắt flash sale", "success")
    return redirect(url_for("admin.flash_sales"))

@admin_bp.route("/flash-sales/<int:sale_id>/delete", methods=["POST"])
@admin_required
def delete_flash_sale(sale_id: int):
    sale = FlashSale.query.get_or_404(sale_id)
    owner_id = None
    if sale.variant and sale.variant.product and sale.variant.product.shop:
        owner_id = sale.variant.product.shop.owner_id


    _log("DELETE_FLASH_SALE", f"flash_sale_{sale.id}")
    if owner_id:
        _notify(owner_id, "Flash sale bị xóa", "Flash sale của bạn đã bị xóa bởi Admin")

    db.session.delete(sale)
    db.session.commit()
    flash("Đã xóa flash sale", "success")
    return redirect(url_for("admin.flash_sales"))

@admin_bp.route("/audit-logs")
@admin_required
def audit_logs():
    action_filter = (request.args.get("action") or "ALL").upper()
    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    if action_filter != "ALL":
        query = query.filter(AuditLog.action == action_filter)


    logs = query.limit(200).all()
    actions = [r[0] for r in db.session.query(AuditLog.action).distinct().order_by(AuditLog.action).all()]
    users = {u.id: u for u in User.query.filter(User.id.in_([l.user_id for l in logs if l.user_id])).all()}

    return render_template("admin/audit_logs.html", logs=logs, actions=actions, action_filter=action_filter, users=users)