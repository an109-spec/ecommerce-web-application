from functools import wraps
from flask import session, redirect, url_for, flash, request
from app.common.exceptions import ForbiddenError
from app.models import User

def require_role(*roles: str):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            user_id = session.get("user_id")

            if not user_id:
                raise ForbiddenError("Login required")

            user = User.query.get(user_id)

            if not user:
                raise ForbiddenError("User not found")
            
            if user.is_banned:
                raise ForbiddenError("Tài khoản của bạn đã bị khóa")

            if user.role not in roles:
                raise ForbiddenError("Permission denied")

            return func(*args, **kwargs)

        return wrapper

    return decorator

def seller_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        user_id = session.get("user_id")

        if not user_id:
            return redirect(url_for("auth.login", role="seller"))
        

        user = User.query.get(user_id)

        if not user:
            return redirect(url_for("auth.login", role="seller"))
        
        if user.is_banned:
            flash("Tài khoản của bạn đã bị khóa. Liên hệ admin để mở khóa.", "danger")
            return redirect(url_for("home.home_page"))

        shop = user.shop

        if not shop:
            flash("Bạn cần đăng ký người bán trước", "warning")
            return redirect(url_for("seller.register_shop"))
        
        allow_dashboard = request.endpoint == "seller.dashboard"

        if shop.status == "BANNED" and not allow_dashboard:
            flash("Shop của bạn đã bị khóa. Liên hệ admin để mở khóa.", "danger")
            return redirect(url_for("home.home_page"))

        if shop.status == "PENDING" and not allow_dashboard:
            flash("Shop đang chờ admin duyệt. Vui lòng quay lại sau.", "warning")
            return redirect(url_for("home.home_page"))

        if not shop.onboarding_completed:
            return redirect(url_for("seller.setup_shipping"))

        return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    return require_role("admin")(func)