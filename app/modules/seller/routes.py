import os
import uuid
from decimal import Decimal
from flask import (
    render_template,
    request,
    redirect,
    session,
    jsonify,
    url_for,
    flash,
    current_app,
)
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import User, Product, Category, ProductVariant, FlashSale, order
from app.common.security.permission import seller_required
from app.common.exceptions import ValidationError, AppException
from app.modules.order.service import OrderService
from app.modules.product.service import ProductService
from . import seller_bp
from .dto import CreateShopDTO, ShippingSetupDTO
from .service import SellerService
from .center_service import SellerCenterService
from .product_service import SellerProductService, SellerProductCreateDTO

from .repository import SellerRepository
from app.modules.promotion.repository import FlashSaleRepository
from app.models.product import ProductCategory,ProductImage
from app.modules.promotion.service import VoucherService, PromotionService
from app.utils.time import utcnow
from app.models.voucher import Voucher

now = utcnow()
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def get_current_shop(user):
    if not user:
        return None
    return user.shop


def _build_steps(shop):
    active_step = shop.onboarding_step if shop else 1
    labels = ["Thông tin Shop", "Cài đặt vận chuyển"]

    return [
        {
            "label": label,
            "index": i + 1,
            "active": i + 1 == active_step,
        }
        for i, label in enumerate(labels)
    ]


@seller_bp.route("/")
def seller_center():
    user = get_current_user()

    if not user:
        return redirect(url_for("auth.login", next="/seller", role="seller"))

    shop = get_current_shop(user)

    if not shop:
        return redirect(url_for("seller.register_shop"))

    if not shop.onboarding_completed:
        return redirect(url_for("seller.setup_shipping"))

    return redirect(url_for("seller.dashboard"))


@seller_bp.route("/register_shop", methods=["GET", "POST"])
def register_shop():
    user = get_current_user()

    if not user:
        return redirect(
            url_for(
                "auth.login",
                next=url_for("seller.register_shop"),
                role="seller",
            )
        )

    shop = get_current_shop(user)

    if shop:
        if not shop.onboarding_completed:
            return redirect(url_for("seller.setup_shipping"))

        return redirect(url_for("seller.dashboard"))

    if request.method == "GET":

        form = {}

        if shop:
            form = {
                "name": shop.name,
                "pickup_address": shop.pickup_address,
                "email": shop.contact_email,
                "phone": shop.contact_phone,
            }

        return render_template(
            "seller/shop/register_shop.html",
            steps=_build_steps(shop),
            form=form,
        )

    form = {
        "name": (request.form.get("name") or "").strip(),
        "pickup_address": (request.form.get("pickup_address") or "").strip(),
        "email": (request.form.get("email") or "").strip(),
        "phone": (request.form.get("phone") or "").strip(),
    }

    try:
        dto = CreateShopDTO(**form)

        if shop:
            SellerService.update_shop(shop, dto)
        else:
            SellerService.register_shop(user, dto)

    except ValidationError as e:
        return render_template(
            "seller/shop/register_shop.html",
            steps=_build_steps(shop),
            error=str(e),
            form=form,
        )

    return redirect(url_for("seller.setup_shipping"))

@seller_bp.route("/api/shop", methods=["PUT"])
@seller_required
def update_shop_api():

    user = get_current_user()
    shop = get_current_shop(user)

    if not shop:
        return jsonify({"success": False}), 404

    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    address = request.form.get("address")

    logo = request.files.get("logo")

    try:

        dto = CreateShopDTO(
            name=name,
            pickup_address=address,
            email=email,
            phone=phone
        )

        SellerService.update_shop(shop, dto)

        if logo and logo.filename:

            filename = secure_filename(logo.filename)
            unique = str(uuid.uuid4()) + "_" + filename

            upload_folder = os.path.join(
                current_app.root_path,
                "static/uploads/shops"
            )

            os.makedirs(upload_folder, exist_ok=True)

            path = os.path.join(upload_folder, unique)

            logo.save(path)

            shop.logo = f"/static/uploads/shops/{unique}"

            db.session.commit()

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

    return jsonify({"success": True})

@seller_bp.route("/setup_shipping", methods=["GET", "POST"])
def setup_shipping():
    user = get_current_user()

    if not user:
        return redirect(
            url_for(
                "auth.login",
                next=url_for("seller.setup_shipping"),
                role="seller",
            )
        )

    shop = get_current_shop(user)

    if not shop:
        return redirect(url_for("seller.register_shop"))

    if request.method == "POST":

        try:
            dto = ShippingSetupDTO(
                fast=request.form.get("hoa_toc") == "on",
                same_day=request.form.get("trong_ngay") == "on",
                express=request.form.get("nhanh") == "on",
                self_delivery=request.form.get("tu_nhan") == "on",
                pickup_point=request.form.get("pickup_point") == "on",
                bulky=request.form.get("cong_kenh") == "on",
            )

            SellerService.setup_shipping(shop, dto)

        except ValidationError as e:
            return render_template(
                "seller/shop/shipping_setup.html",
                shop=shop,
                steps=_build_steps(shop),
                error=str(e),
            )

        return redirect(url_for("seller.dashboard"))

    return render_template(
        "seller/shop/shipping_setup.html",
        shop=shop,
        steps=_build_steps(shop),
    )

def check_onboarding(shop):
    if not shop:
        flash("Bạn cần đăng ký người bán trước", "warning")
        return redirect(url_for("seller.register_shop"))

    if not shop.onboarding_completed:
        return redirect(url_for("seller.setup_shipping"))
    return None

@seller_bp.route("/dashboard")
@seller_required
def dashboard():
    user = get_current_user()
    shop = get_current_shop(user)
    redirect_url = check_onboarding(shop)

    if redirect_url:
        return redirect(redirect_url)
    data = SellerCenterService.get_dashboard(shop.id)

    return render_template(
        "seller/dashboard.html",
        shop=shop,
        todo=data["todo"],
        today_revenue=data["today_revenue"],
        total_orders=data["total_orders"],
        total_products=data["total_products"],
        total_reviews=data["total_reviews"],
        recent_orders=data["recent_orders"],
    )


@seller_bp.route("/products")
@seller_required
def product_list():
    user = get_current_user()
    shop = get_current_shop(user)

    products = SellerProductService.list_products(shop.id)

    return render_template(
        "seller/product/product_list.html",
        products=products,
    )


@seller_bp.route("/products/create", methods=["GET", "POST"])
@seller_required
def create_product():

    user = get_current_user()
    shop = get_current_shop(user)

    categories = Category.query.all()

    if request.method == "GET":
        return render_template(
            "seller/product/product_create.html",
            categories=categories,
            form=None,
            error=None
        )

    try:

        name = request.form.get("name")
        description = request.form.get("description")
        category_ids = request.form.getlist("category_ids")

        if not name:
            raise ValueError("Tên sản phẩm không được để trống")

        if not category_ids:
            raise ValueError("Phải chọn danh mục")

        prices = request.form.getlist("variant_price[]")
        stocks = request.form.getlist("variant_stock[]")
        sizes = request.form.getlist("variant_size[]")
        colors = request.form.getlist("variant_color[]")
        variant_images = request.files.getlist("variant_image[]")

        count = min(len(prices), len(stocks), len(sizes), len(colors))

        if count == 0:
            raise ValueError("Phải có ít nhất 1 phân loại")

        upload_folder = os.path.join(
            current_app.root_path,
            "static/uploads/products"
        )

        os.makedirs(upload_folder, exist_ok=True)

        variants = []

        shipping_fast = request.form.get("shipping_fast")
        shipping_same_day = request.form.get("shipping_same_day")
        shipping_express = request.form.get("shipping_express")
        shipping_pickup = request.form.get("shipping_pickup")
        shipping_bulky = request.form.get("shipping_bulky")

        shipping_fast_fee = int(request.form.get("shipping_fast_fee") or 0)
        shipping_same_day_fee = int(request.form.get("shipping_same_day_fee") or 0)
        shipping_express_fee = int(request.form.get("shipping_express_fee") or 0)
        shipping_pickup_fee = int(request.form.get("shipping_pickup_fee") or 0)
        shipping_bulky_fee = int(request.form.get("shipping_bulky_fee") or 0)

        weight = int(request.form.get("weight") or 0)
        length = int(request.form.get("length") or 0)
        width = int(request.form.get("width") or 0)
        height = int(request.form.get("height") or 0)
        for i in range(count):

            price = Decimal(prices[i] or 0)
            stock = int(stocks[i] or 0)
            size = sizes[i]
            color = colors[i]

            image_url = None

            if i < len(variant_images):
                img = variant_images[i]

                if img and img.filename:

                    filename = secure_filename(img.filename)
                    unique = str(uuid.uuid4()) + "_" + filename

                    path = os.path.join(upload_folder, unique)

                    img.save(path)

                    image_url = f"/static/uploads/products/{unique}"

            variants.append({
                "price": price,
                "stock": stock,
                "image": image_url,

                "weight": weight,
                "length": length,
                "width": width,
                "height": height,

                "shipping_fast_fee": shipping_fast_fee if shipping_fast else 0,
                "shipping_same_day_fee": shipping_same_day_fee if shipping_same_day else 0,
                "shipping_express_fee": shipping_express_fee if shipping_express else 0,
                "shipping_pickup_fee": shipping_pickup_fee if shipping_pickup else 0,
                "shipping_bulky_fee": shipping_bulky_fee if shipping_bulky else 0,

                "attributes": {
                    "size": size,
                    "color": color
                }
            })

        # upload product images
        product_images = request.files.getlist("images[]")

        if len(product_images) > 9:
            raise ValueError("Tối đa 9 ảnh sản phẩm")

        images = []

        for file in product_images:

            if file and file.filename:

                filename = secure_filename(file.filename)
                unique = str(uuid.uuid4()) + "_" + filename

                path = os.path.join(upload_folder, unique)

                file.save(path)

                images.append(
                    f"/static/uploads/products/{unique}"
                )

        dto = SellerProductCreateDTO(
            name=name,
            description=description,
            category_ids=[int(cid) for cid in category_ids],
            images=images,
            variants=variants
        )

        SellerProductService.create(shop.id, dto)

        return redirect(url_for("seller.product_list"))

    except (TypeError, ValueError) as e:

        return render_template(
            "seller/product/product_create.html",
            categories=categories,
            error=str(e),
            form=request.form
        )

    except AppException as e:

        return render_template(
            "seller/product/product_create.html",
            categories=categories,
            error=str(e),
            form=request.form
        )

@seller_bp.route("/products/<int:pid>/delete")
@seller_required
def delete_product(pid):

    user = get_current_user()
    shop = get_current_shop(user)

    product = Product.query.filter_by(
        id=pid,
        shop_id=shop.id,
    ).first_or_404()

    db.session.delete(product)
    db.session.commit()

    flash("Xóa sản phẩm thành công!", "success")

    return redirect(url_for("seller.product_list"))


@seller_bp.route("/products/<int:pid>/edit", methods=["GET", "POST"])
@seller_required
def edit_product(pid):

    user = get_current_user()
    shop = get_current_shop(user)

    product = SellerRepository.get_product(shop.id, pid)

    if not product:
        raise AppException("Product not found")

    if request.method == "GET":

        categories = Category.query.all()

        return render_template(
                "seller/product/product_edit.html",
            product=product,
            variants=product.variants,
            images=product.images,
            categories=categories
            )

    try:

        name = request.form.get("name")
        description = request.form.get("description")
        category_ids = [
            int(category_id)
            for category_id in request.form.getlist("category_ids[]")
            if category_id
        ]
        product.product_categories.clear()
        for idx, category_id in enumerate(category_ids):
            product.product_categories.append(
                ProductCategory(
                    category_id=category_id,
                    is_primary=(idx == 0),
                )
            )
        shipping_fast = request.form.get("shipping_fast")
        shipping_same_day = request.form.get("shipping_same_day")
        shipping_express = request.form.get("shipping_express")
        shipping_pickup = request.form.get("shipping_pickup")
        shipping_bulky = request.form.get("shipping_bulky")

        shipping_fast_fee = int(request.form.get("shipping_fast_fee") or 0)
        shipping_same_day_fee = int(request.form.get("shipping_same_day_fee") or 0)
        shipping_express_fee = int(request.form.get("shipping_express_fee") or 0)
        shipping_pickup_fee = int(request.form.get("shipping_pickup_fee") or 0)
        shipping_bulky_fee = int(request.form.get("shipping_bulky_fee") or 0)

        weight = float(request.form.get("weight") or 0)
        length = float(request.form.get("length") or 0)
        width = float(request.form.get("width") or 0)
        height = float(request.form.get("height") or 0)

        variants = []

        prices = request.form.getlist("variant_price[]")
        stocks = request.form.getlist("variant_stock[]")
        sizes = request.form.getlist("variant_size[]")
        colors = request.form.getlist("variant_color[]")
        variant_images = request.files.getlist("variant_image[]")
        old_images = request.form.getlist("variant_old_image[]")
        for i in range(len(prices)):

            price = prices[i]
            stock = stocks[i]
            size = sizes[i]
            color = colors[i]

            if not price or not stock:
                continue
            image = None
            if i < len(variant_images):
                file = variant_images[i]

                if file and file.filename != "":
                    image = file
                else:
                    image = old_images[i] if i < len(old_images) else None
            variants.append({
                "price": Decimal(price),
                "stock": int(stock),
                "image": image,
                "weight": weight,
                "length": length,
                "width": width,
                "height": height,

                "shipping_fast_fee": shipping_fast_fee if shipping_fast else 0,
                "shipping_same_day_fee": shipping_same_day_fee if shipping_same_day else 0,
                "shipping_express_fee": shipping_express_fee if shipping_express else 0,
                "shipping_pickup_fee": shipping_pickup_fee if shipping_pickup else 0,
                "shipping_bulky_fee": shipping_bulky_fee if shipping_bulky else 0,

                "attributes": {
                    "size": size,
                    "color": color
                }
            })
        if not variants:
            raise Exception("Sản phẩm phải có ít nhất 1 phân loại")
        SellerProductService.update_variants(
            shop.id,
            pid,
            name,
            description,
            variants
        )
        images = request.files.getlist("images[]")
        image_urls = []
        for img in images:
            if img.filename == "":
                continue

            filename = str(uuid.uuid4()) + "_" + secure_filename(img.filename)
            save_path = os.path.join("app/static/uploads/products", filename)
            img.save(save_path)
            image_urls.append(f"/static/uploads/products/{filename}")
        if image_urls:
            SellerRepository.create_product_images(pid,image_urls)
            product.thumbnail = image_urls[0]

    except Exception as e:
        db.session.rollback()
        categories = Category.query.all()
        return render_template(
            "seller/product/product_edit.html",
            product=product,
            variants=product.variants,
            categories=categories,
            error=str(e),
        )
    db.session.commit() 
    flash("Cập nhật sản phẩm thành công", "success")
    return redirect(url_for("seller.product_list"))

@seller_bp.route("/products/image/delete", methods=["POST"])
@seller_required
def delete_product_image():

    data = request.get_json()

    image_url = data.get("image_url")

    if not image_url:
        return jsonify({"error": "No image url"}), 400

    from os.path import basename

    image_name = basename(image_url)
    img = ProductImage.query.filter(
        (ProductImage.image_url == image_url)
        | (ProductImage.image_url == image_name)
        | (ProductImage.image_url.like(f"%/{image_name}"))
    ).first()

    if img:
        product_id = img.product_id
        image_name = basename(img.image_url)
        file_path = os.path.join(
        "app/static/uploads/products",
        image_name
    )
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print("Delete file error:", e)

        db.session.delete(img)
        db.session.flush()

        # 👇 THÊM KHÚC NAYF
        first_img = ProductImage.query.filter_by(product_id=product_id).first()
        product = Product.query.get(product_id)

        if product:
            product.thumbnail = first_img.image_url if first_img else None

        db.session.commit()
    return jsonify({"success": True})

@seller_bp.route("/products/<int:pid>/hide")
@seller_required
def hide_product(pid):

    user = get_current_user()
    shop = get_current_shop(user)

    SellerProductService.update_status(shop.id, pid, "HIDDEN")

    return redirect(url_for("seller.product_list"))


@seller_bp.route("/products/<int:pid>/activate")
@seller_required
def activate_product(pid):

    user = get_current_user()
    shop = get_current_shop(user)

    SellerProductService.update_status(shop.id, pid, "ACTIVE")

    return redirect(url_for("seller.product_list"))

@seller_bp.route("/products/<int:pid>/restock", methods=["POST"])
@seller_required
def restock_product(pid):

    user = get_current_user()
    shop = get_current_shop(user)

    quantity = request.form.get("quantity")

    if not quantity:
        flash("Vui lòng nhập số lượng", "error")
        return redirect(url_for("seller.product_list"))

    quantity = int(quantity)

    SellerProductService.restock(shop.id, pid, quantity)

    flash("Nhập kho thành công", "success")

    return redirect(url_for("seller.product_list"))


@seller_bp.route("/orders")
@seller_required
def orders_page():

    user = get_current_user()
    shop = get_current_shop(user)

    status = request.args.get("status")
    if status:
        status = status.lower()
    orders = SellerCenterService.list_orders(shop.id, status)
    from app.modules.order.service import OrderService
    for order in orders:
        customer = OrderService.get_customer_info(order)
        order.display_name = customer['name']
        order.display_phone = customer['phone']
    return render_template(
        "seller/order/order_list.html",
        orders=orders,
        status=status or "ALL",
    )


@seller_bp.route("/chat")
@seller_required
def chat_page():

    user = get_current_user()
    from app.modules.chat.service import ChatService

    room_query = request.args.get("room", type=int)
    rooms = ChatService.list_rooms_for_user(user.id, seller_only=True)
    active = None
    if room_query:
        active = next((item for item in rooms if item["room"].id == room_query), None)
    if not active and rooms:
        active = rooms[0]

    messages = []
    if active:
        messages = ChatService.get_chat_history(active["room"].id, limit=200)

    return render_template(
        "seller/chat.html",
        rooms=rooms,
        active=active,
        messages=messages,
        current_user=user,
    )
################
#
# PROMOTIONS   
#
################
@seller_bp.route("/promotions")
@seller_required
def promotions_page():

    user = get_current_user()
    shop = get_current_shop(user)

    promotions = PromotionService.list_promotions(shop.id)

    return render_template(
        "seller/promotion/promotion_list.html",
        promotions=promotions,
        now=utcnow()
    )
@seller_bp.route("/promotions/create")
@seller_required
def promotion_create_page():

    user = get_current_user()
    shop = get_current_shop(user)

    products = Product.query.filter_by(
        shop_id=shop.id
    ).all()

    return render_template(
        "seller/promotion/promotion_create.html",
        products=products
    )
@seller_bp.route("/promotions/<int:pid>/delete")
@seller_required
def delete_promotion(pid):

    PromotionService.delete_promotion(pid)

    return redirect("/seller/promotions")

@seller_bp.route("/promotions/<int:id>/edit", methods=["GET", "POST"])
@seller_required
def edit_promotion_page(id):

    user = get_current_user()
    shop = get_current_shop(user)

    promotion = PromotionService.get_promotion(id)

    if request.method == "POST":

        name = request.form["name"]
        discount = int(request.form["discount_percent"])

        start = datetime.fromisoformat(request.form["start_time"])
        end = datetime.fromisoformat(request.form["end_time"])

        PromotionService.update_promotion(
            id,
            name,
            discount,
            start,
            end
        )

        return redirect("/seller/promotions")

    products = ProductService.get_products_by_shop(shop.id)

    return render_template(
        "seller/promotion/promotion_edit.html",
        promotion=promotion,
        products=products
    )
##############
#
# flash-sales
#
##############
@seller_bp.route("/flash-sales")
@seller_required
def flash_sales_page():

    user = get_current_user()
    shop = get_current_shop(user)

    sales = FlashSaleRepository.list_flash_sales_for_shop(shop.id)

    return render_template(
        "seller/promotion/flash_sale_list.html",
        sales=sales
    )

@seller_bp.route("/flash-sales/create")
@seller_required
def flash_sale_create_page():

    user = get_current_user()
    shop = get_current_shop(user)

    from app.models.product import Product

    products = Product.query.filter_by(
        shop_id=shop.id
    ).all()

    return render_template(
        "seller/promotion/flash_sale_create.html",
        products=products
    )

@seller_bp.route("/flash-sales/<int:flash_id>/edit")
@seller_required
def flash_sale_edit_page(flash_id):
    user = get_current_user()
    shop = get_current_shop(user)
    flash = FlashSale.query.get_or_404(flash_id)
    products = Product.query.filter_by(shop_id=shop.id).all()
    return render_template(
        "seller/promotion/flash_sale_edit.html",
        flash=flash,
        products=products
    )

@seller_bp.route("/flash-sales/<int:flash_id>/delete", methods=["POST"])
@seller_required
def flash_sale_delete(flash_id):

    FlashSaleRepository.delete_flash_sale(flash_id)

    db.session.commit()

    return {"success": True}

@seller_bp.route("/revenue")
@seller_required
def revenue_page():

    user = get_current_user()
    shop = get_current_shop(user)

    summary = SellerCenterService.get_revenue_summary(shop.id)

    return render_template(
        "seller/revenue.html",
        summary=summary,
    )

@seller_bp.route("/shop-settings")
@seller_required
def shop_settings_page():

    user = get_current_user()
    shop = get_current_shop(user)

    return render_template(
        "seller/shop/settings.html",
        shop=shop,
    )


@seller_bp.route("/become")
def become_seller():

    user = get_current_user()

    if not user:
        return redirect(
            url_for(
                "auth.login",
                next=url_for("seller.register_shop"),
                role="seller",
            )
        )

    if user.is_seller:
        return redirect(url_for("seller.seller_center"))

    return redirect(url_for("seller.register_shop"))

@seller_bp.route("/api/product/<int:product_id>/variants")
@seller_required
def get_variants(product_id):
    from datetime import timezone
    from app.models.flash_sale import FlashSale

    variants = ProductVariant.query.filter_by(
        product_id=product_id
    ).all()
    now = datetime.now(timezone.utc)
    data = []

    for v in variants:
        reserved = (
            db.session.query(db.func.coalesce(db.func.sum(FlashSale.stock_limit - FlashSale.sold_count), 0))
            .filter(
                FlashSale.variant_id == v.id,
                FlashSale.is_active == True,
                FlashSale.end_time >= now,
            )
            .scalar()
        )
        available_stock = max(v.stock - int(reserved or 0), 0)
        data.append({
            "id": v.id,
            "size": v.get_attr("size"),
            "color": v.get_attr("color"),
            "stock": available_stock,
            "total_stock": v.stock,
            "price": float(v.price)
            })

    return jsonify(data)

##########
#        # 
#VOUCHERS#
#        #
##########
@seller_bp.route("/vouchers")
@seller_required
def voucher_page():

    user = get_current_user()
    shop = get_current_shop(user)

    vouchers = VoucherService.list_vouchers(shop.id)

    return render_template(
        "seller/promotion/voucher_list.html",
        vouchers=vouchers, 
        now=utcnow()
    )
@seller_bp.route("/vouchers/create")
@seller_required
def voucher_create_page():
    user = get_current_user()
    shop = get_current_shop(user)

    products = Product.query.filter_by(
        shop_id=shop.id
    ).all()

    return render_template(
        "seller/promotion/voucher_create.html",
        products=products
    )

@seller_bp.route("/vouchers/create", methods=["POST"])
@seller_required
def voucher_create():

    user = get_current_user()
    shop = get_current_shop(user)

    VoucherService.create_voucher(
        shop_id=shop.id,
        name=request.form["name"],
        code=request.form["code"],
        discount_type=request.form["discount_type"],
        discount_value=int(request.form["discount_value"]),
        min_order_value=int(request.form["min_order_value"]),
        usage_limit=int(request.form["usage_limit"]),
        start_time=datetime.fromisoformat(request.form["start_time"]),
        end_time=datetime.fromisoformat(request.form["end_time"]),
    )
    return redirect("/seller/vouchers")

@seller_bp.route("/api/voucher/create", methods=["POST"])
@seller_required
def voucher_create_api():

    data = request.get_json() or {}

    user = get_current_user()
    shop = get_current_shop(user)

    try:
        VoucherService.create_voucher(
            shop_id=shop.id,
            name=data["name"],
            code=data["code"],
            discount_type=data["discount_type"],
            discount_value=int(data["discount_value"]),
            min_order_value=int(data["min_order_value"]),
            usage_limit=int(data["usage_limit"]),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return jsonify({"success": True})


@seller_bp.route("/vouchers/<int:voucher_id>/edit")
@seller_required
def voucher_edit_page(voucher_id):
    user = get_current_user()
    shop = get_current_shop(user)
    voucher = Voucher.query.get_or_404(voucher_id)
    products = Product.query.filter_by(shop_id=shop.id).all()

    return render_template(
        "seller/promotion/voucher_edit.html",
        voucher=voucher,
        products=products,
        view_only=False
    )


@seller_bp.route("/vouchers/<int:voucher_id>/view")
@seller_required
def voucher_view_page(voucher_id):
    user = get_current_user()
    shop = get_current_shop(user)
    voucher = Voucher.query.get_or_404(voucher_id)
    products = Product.query.filter_by(shop_id=shop.id).all()
    return render_template(
        "seller/promotion/voucher_edit.html",
        voucher=voucher,
        products=products,
        view_only=True
    )

@seller_bp.route("/vouchers/<int:voucher_id>/edit", methods=["POST"])
@seller_required
def voucher_update(voucher_id):

    VoucherService.update_voucher(
        voucher_id=voucher_id,
        name=request.form["name"],
        code=request.form["code"],
        discount_type=request.form["discount_type"],
        discount_value=int(request.form["discount_value"]),
        min_order_value=int(request.form["min_order_value"]),
        usage_limit=int(request.form["usage_limit"]),
        start_time=datetime.fromisoformat(request.form["start_time"]),
        end_time=datetime.fromisoformat(request.form["end_time"]),
    )
    return redirect("/seller/vouchers")

@seller_bp.route("/vouchers/<int:voucher_id>/delete")
@seller_required
def voucher_delete(voucher_id):
    VoucherService.delete_voucher(voucher_id)
    return redirect("/seller/vouchers?deleted=1")

@seller_bp.route("/vouchers/<int:voucher_id>/toggle")
@seller_required
def voucher_toggle(voucher_id):
    VoucherService.toggle_voucher(voucher_id)
    return redirect("/seller/vouchers")

@seller_bp.route("/api/flash-sales/<int:flash_id>/update", methods=["POST"])
@seller_required
def update_flash_sale(flash_id):
    data = request.get_json() or {}

    flash_sale = FlashSale.query.get_or_404(flash_id)

    try:
        flash_sale.discount_percent = data.get("discount_percent")
        flash_sale.start_time = datetime.fromisoformat(data.get("start_time"))
        flash_sale.end_time = datetime.fromisoformat(data.get("end_time"))

        db.session.commit()

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return jsonify({"success": True})