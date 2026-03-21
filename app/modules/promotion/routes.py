from flask import jsonify, request, redirect, render_template
from datetime import datetime, timezone
from . import promotion_bp
from .service import FlashSaleService, VoucherService, PromotionService

@promotion_bp.route("/api/promotion/create", methods=["POST"])
def create_promotion():

    data = request.form

    variant_ids = request.form.getlist("variant_ids[]")

    for vid in variant_ids:

        PromotionService.create_promotion(
            name=data["name"],
            variant_id=int(vid),
            discount_percent=int(data["discount_percent"]),
            start_time=datetime.fromisoformat(data["start_time"]).astimezone(timezone.utc),
            end_time=datetime.fromisoformat(data["end_time"]).astimezone(timezone.utc)
        )

    return redirect("/seller/promotions")


@promotion_bp.route("/api/flash-sale/create", methods=["POST"])
def create_flash_sale():

    data = request.get_json() or request.form

    try:
        sale = FlashSaleService.create_flash_sale(
            variant_id=int(data["variant_id"]),
            discount_percent=int(data["discount_percent"]),
            stock_limit=int(data["stock_limit"]),
            start_time=datetime.fromisoformat(data["start_time"]).replace(tzinfo=timezone.utc),
            end_time=datetime.fromisoformat(data["end_time"]).replace(tzinfo=timezone.utc),
        )

        return jsonify({
            "success": True,
            "id": sale.id
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    

@promotion_bp.route("/api/voucher/create", methods=["POST"])
def create_voucher():

    data = request.get_json() or request.form

    voucher = VoucherService.create_voucher(
        code=data["code"],
        discount_type=data["discount_type"],
        discount_value=data["discount_value"],
        quantity=data["quantity"],
        min_order=data["min_order"],
        expired_at=datetime.fromisoformat(data["expired_at"]),
    )

    return jsonify({"id": voucher.id})


@promotion_bp.route("/api/promotion/<int:pid>", methods=["DELETE"])
def delete_promotion(pid):
    PromotionService.delete_promotion(pid)
    return jsonify({"success": True})

@promotion_bp.route("/flash-sales")
def flash_sales():

    sales = FlashSaleService.get_active_flash_sales()

    return jsonify([
        {
            "variant_id": s.variant_id,
            "price": s.discount_price
        }
        for s in sales
    ])


@promotion_bp.route("/voucher/validate", methods=["POST"])
def validate_voucher():

    code = request.json["code"]

    voucher = VoucherService.validate_voucher(code)

    if not voucher:
        return jsonify({"valid": False})

    return jsonify({
        "valid": True,
        "discount": float(voucher.discount_value)
    })
@promotion_bp.route("/api/promotions")
def promotions():

    promos = PromotionService.get_active_promotions()

    return jsonify([
        {
            "variant_id":p.variant_id,
            "discount_percent":p.discount_percent
        }
        for p in promos
    ])


@promotion_bp.route("/api/flash-sale/<int:flash_id>/update", methods=["POST"])
def update_flash_sale(flash_id):

    data = request.get_json()

    try:

        start_time = datetime.fromisoformat(data["start_time"])
        end_time = datetime.fromisoformat(data["end_time"])

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        FlashSaleService.update_flash_sale(
            flash_id=flash_id,
            discount_percent=int(data["discount_percent"]),
            stock_limit=int(data["stock_limit"]),
            start_time=start_time,
            end_time=end_time,
        )

        return jsonify({"success": True})

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@promotion_bp.route("/vouchers", methods=["GET"])
def public_vouchers():
    from app.models.voucher import Voucher
    vouchers = VoucherService.list_public_active_vouchers()
    return render_template("promotion/voucher_list.html", vouchers=vouchers)