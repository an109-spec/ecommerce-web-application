from flask import jsonify, redirect, render_template, request, url_for
from . import cart_bp
from .service import CartService


def _wants_json_response() -> bool:
    if request.is_json:
        return True
    if request.args.get("format") == "json":
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept or request.headers.get("X-Requested-With") == "XMLHttpRequest"


@cart_bp.route("/", methods=["GET"])
def view_cart():
    payload = CartService.build_cart_payload()
    if _wants_json_response():
        return jsonify(payload)
    return render_template("cart/cart.html", cart_payload=payload, summary=CartService.get_summary())


@cart_bp.route("/mini", methods=["GET"])
def mini_cart():
    return jsonify(CartService.get_mini_cart())


@cart_bp.route("/item/<int:variant_id>", methods=["GET"])
def get_item(variant_id: int):
    try:
        return jsonify(CartService.get_cart_item_details(variant_id))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404


@cart_bp.route("/add", methods=["POST"])
def add():
    payload = request.get_json(silent=True) or request.form
    try:
        response = CartService.add_to_cart(
            product_id=int(payload.get("product_id")),
            quantity=int(payload.get("quantity", 1)),
            variant_id=int(payload.get("variant_id")) if payload.get("variant_id") else None,
            size=payload.get("size"),
            color=payload.get("color"),
        )
        if _wants_json_response():
            return jsonify(response), 200
        return redirect(url_for("cart.view_cart"))
    except (TypeError, ValueError) as exc:
        if _wants_json_response():
            return jsonify({"error": str(exc)}), 422
        raise

@cart_bp.route("/item/<int:variant_id>", methods=["PUT"])
def update_item(variant_id: int):
    payload = request.get_json(silent=True) or {}
    try:
        response = CartService.update_item(
            variant_id,
            quantity=int(payload.get("quantity", 1)),
            variant_id=int(payload.get("variant_id")) if payload.get("variant_id") else None,
            size=payload.get("size"),
            color=payload.get("color"),
        )
        return jsonify(response), 200
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 422


@cart_bp.route("/item/<int:variant_id>", methods=["DELETE"])
def delete_item(variant_id: int):
    try:
        return jsonify(CartService.remove_item(variant_id)), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422


@cart_bp.route("/remove/<int:variant_id>", methods=["POST"])
def remove(variant_id: int):
    CartService.remove_item(variant_id)
    if _wants_json_response():
        return jsonify(CartService.build_cart_payload()), 200
    return redirect(url_for("cart.view_cart"))

from app.common.exceptions import AppException   # thêm dòng này trên đầu file

@cart_bp.route("/voucher/apply", methods=["POST"])
def apply_voucher():
    payload = request.get_json(silent=True) or request.form
    try:
        response = CartService.apply_voucher(
            int(payload.get("shop_id")),
            int(payload.get("voucher_id"))
        )

        if _wants_json_response():
            return jsonify(response), 200
        return redirect(url_for("cart.view_cart"))

    except AppException as exc:   # ✅ BẮT ĐÚNG LOẠI LỖI
        if _wants_json_response():
            return jsonify({"error": str(exc)}), exc.status_code
        return redirect(url_for("cart.view_cart"))

    except (TypeError, ValueError) as exc:
        if _wants_json_response():
            return jsonify({"error": str(exc)}), 422
        raise

    except Exception as e:
        print("ERROR APPLY VOUCHER:", e)
        return jsonify({"error": "Lỗi server"}), 500

@cart_bp.route("/clear", methods=["POST"])
def clear():
    CartService.clear_cart()
    if _wants_json_response():
        return jsonify({"message": "Cart cleared"}), 200
    return redirect(url_for("cart.view_cart"))