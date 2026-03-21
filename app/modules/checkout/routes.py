from flask import jsonify, render_template, request, session, redirect, url_for

from app.common.exceptions import AppException

from . import checkout_bp
from .service import CheckoutService


def _resolve_user_id() -> int:
    user_id = session.get("user_id")
    if not user_id:
        raise AppException("Bạn chưa đăng nhập", status_code=401)
    return int(user_id)


@checkout_bp.route("", methods=["GET"])
def checkout_page():
    if not session.get("user_id"):
        return redirect(url_for("auth.login", next=request.url))
    try:
        payload = CheckoutService.get_current_checkout(_resolve_user_id(), auto_init_from_cart=True)
        return render_template("checkout/index.html", checkout_payload=payload)
    except AppException:
        return render_template("checkout/index.html", checkout_payload=None)


@checkout_bp.route("/init", methods=["GET", "POST"])
def init_checkout():
    try:
        user_id = _resolve_user_id()
        payload = request.get_json(silent=True) if request.method == "POST" else None
        data = CheckoutService.init_checkout(user_id, payload)
        return jsonify(data), 200
    except AppException as exc:
        return jsonify({"error": str(exc)}), exc.status_code


@checkout_bp.route("/data", methods=["GET"])
def checkout_data():
    try:
        user_id = _resolve_user_id()
        # Thêm dòng này để xóa state cũ, ép Service phải tính lại từ giỏ hàng và DB mới nhất
        session.pop('checkout_state', None) 
        
        data = CheckoutService.get_current_checkout(user_id, auto_init_from_cart=True)
        return jsonify(data), 200
    except AppException as exc:
        return jsonify({"error": str(exc)}), exc.status_code


@checkout_bp.route("/apply-voucher", methods=["POST"])
def apply_voucher():
    try:
        user_id = _resolve_user_id()
        payload = request.get_json(silent=True) or {}

        shop_id = payload.get("shop_id")
        voucher_id = payload.get("voucher_id")
        voucher_code = payload.get("voucher_code")

        # ✅ validate trước
        if not shop_id:
            return jsonify({"error": "Thiếu shop_id"}), 422
        if not voucher_code and not voucher_id:
            return jsonify({"error": "Vui lòng nhập mã hoặc chọn voucher"}), 422

        data = CheckoutService.apply_voucher(
            user_id,
            int(shop_id),
            voucher_id=int(voucher_id) if voucher_id else None,
            voucher_code=voucher_code,
        )

        return jsonify(data), 200

    except AppException as exc:
        return jsonify({"error": str(exc)}), exc.status_code

    except (TypeError, ValueError):
        return jsonify({"error": "Dữ liệu voucher không hợp lệ"}), 422


@checkout_bp.route("/shipping-method", methods=["POST"])
def shipping_method():
    try:
        user_id = _resolve_user_id()
        payload = request.get_json(silent=True) or {}
        data = CheckoutService.update_shipping_method(user_id, int(payload.get("shop_id")), payload.get("shipping_method", ""))
        return jsonify(data), 200
    except (TypeError, ValueError):
        return jsonify({"error": "Dữ liệu vận chuyển không hợp lệ"}), 422
    except AppException as exc:
        return jsonify({"error": str(exc)}), exc.status_code


@checkout_bp.route("/payment-method", methods=["POST"])
def payment_method():
    try:
        user_id = _resolve_user_id()
        payload = request.get_json(silent=True) or {}
        data = CheckoutService.update_payment_method(user_id, payload.get("payment_method", ""))
        return jsonify(data), 200
    except AppException as exc:
        return jsonify({"error": str(exc)}), exc.status_code


@checkout_bp.route("/address", methods=["POST"])
def select_address():
    try:
        user_id = _resolve_user_id()
        payload = request.get_json(silent=True) or {}
        data = CheckoutService.update_address(user_id, payload.get("address_id", ""))
        return jsonify(data), 200
    except AppException as exc:
        return jsonify({"error": str(exc)}), exc.status_code

from flask import current_app
@checkout_bp.route("/confirm", methods=["POST"])
def confirm_checkout():
    try:
        user_id = _resolve_user_id()
        payload = request.get_json(silent=True) or {}

        if not payload.get("shop_id"):
            raise AppException("Thiếu shop_id", status_code=422)
        if not payload.get("address_id"):
            raise AppException("Thiếu địa chỉ giao hàng", status_code=422)
        if not payload.get("payment_method"):
            raise AppException("Thiếu phương thức thanh toán", status_code=422)

        data = CheckoutService.confirm_checkout(user_id, payload)
        return jsonify(data), 200

    except AppException as exc:
        return jsonify({"error": str(exc)}), exc.status_code

    except (TypeError, ValueError) as exc:
        current_app.logger.exception("Checkout confirm invalid payload")
        return jsonify({"error": str(exc) or "Dữ liệu đặt hàng không hợp lệ"}), 422

    except Exception:
        current_app.logger.exception("ERROR CONFIRM CHECKOUT")
        return jsonify({"error": "Lỗi server"}), 500