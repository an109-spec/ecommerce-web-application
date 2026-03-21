from flask import jsonify, request, send_file, render_template

from app.common.exceptions import AppException, ValidationError
from decimal import Decimal
from flask import session
from app.models import User
from app.modules.seller.repository import SellerRepository
from app.modules.seller.product_service import SellerProductCreateDTO, SellerProductService, SellerProductUpdateDTO
from app.common.exceptions import ForbiddenError
from . import product_bp
from .dto import ProductCreateDTO, ProductUpdateDTO, ReviewCreateDTO
from .service import ProductService
from .qr_service import export_qr_png, generate_product_qr_by_id
from .shop_service import PublicShopService

@product_bp.route("/shop", methods=["GET"])
def shop_page():
    return render_template("product/list.html")


@product_bp.route("/shop/<int:id>")
def product_detail(id):
    return render_template("product/detail.html", product_id=id)


@product_bp.route("/shop/search", methods=["GET"])
def shop_search_page():
    return render_template("product/search.html")


def _parse_pagination() -> tuple[int, int]:
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        raise ValidationError("page/per_page phải là số nguyên")

    if page < 1:
        raise ValidationError("page phải >= 1")
    if per_page < 1 or per_page > 100:
        raise ValidationError("per_page phải trong khoảng 1-100")

    return page, per_page
@product_bp.route("/shops/<int:shop_id>", methods=["GET"])
def public_shop_page(shop_id: int):
    return render_template("product/shop_public.html", shop_id=shop_id)


@product_bp.route("/shops/<int:shop_id>/summary", methods=["GET"])
def public_shop_summary(shop_id: int):
    try:
        return jsonify(PublicShopService.get_shop_profile(shop_id, session.get("user_id"))), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/shops/<int:shop_id>/products", methods=["GET"])
def public_shop_products(shop_id: int):
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 9))
        if page < 1:
            raise ValidationError("page phải >= 1")
        if limit < 1 or limit > 30:
            raise ValidationError("limit phải trong khoảng 1-30")

        return jsonify(PublicShopService.list_products(
            shop_id,
            filter_by=request.args.get("filter", "all"),
            sort_by=request.args.get("sort", ""),
            page=page,
            limit=limit,
        )), 200
    except ValueError:
        return jsonify({"error": "page/limit phải là số nguyên"}), 422
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/shops/<int:shop_id>/follow", methods=["POST"])
def follow_shop(shop_id: int):
    try:
        return jsonify(PublicShopService.follow(shop_id, session.get("user_id"))), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/shops/<int:shop_id>/follow", methods=["DELETE"])
def unfollow_shop(shop_id: int):
    try:
        return jsonify(PublicShopService.unfollow(shop_id, session.get("user_id"))), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route('/products', methods=['GET'])
def list_products():
    keyword = request.args.get('keyword') or request.args.get('q')
    category_ids = request.args.getlist('category_id')
    freeship = request.args.get('freeship')

    print(f"--- API CHECK: keyword={keyword}, categories={category_ids} ---")

    result = ProductService.list_products(
        keyword=keyword,
        category_ids=category_ids,
        min_price=request.args.get('min_price'),
        max_price=request.args.get('max_price'),
        freeship=freeship,
        sort=request.args.get('sort'),
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 10, type=int)
    )
    return jsonify(result)


@product_bp.route("/products/<int:id>", methods=["GET"])
def get_product_detail(id: int):
    try:
        return jsonify(ProductService.get_product_detail(id)), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/products", methods=["POST"])
def create_product():
    try:
        if not request.is_json:
            raise ValidationError("Request must be JSON")
        dto = ProductCreateDTO.from_dict(request.get_json() or {})
        result = ProductService.create_product(dto)
        return jsonify(result), 201
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/products/<int:id>", methods=["PUT"])
def update_product(id: int):
    try:
        if not request.is_json:
            raise ValidationError("Request must be JSON")
        dto = ProductUpdateDTO.from_dict(request.get_json() or {})
        result = ProductService.update_product(id, dto)
        return jsonify(result), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/products/<int:id>", methods=["DELETE"])
def delete_product(id: int):
    try:
        ProductService.delete_product(id)
        return jsonify({"message": "Xóa sản phẩm thành công"}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/products/<int:id>/reviews", methods=["GET"])
def get_reviews(id: int):
    try:
        from app.modules.product.service import ProductService
        raw_reviews = ProductService.get_product_reviews(id)
        
        processed_reviews = []
        counts = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "comment": 0}
        total_rating = 0

        # Nếu chưa có ai đánh giá
        if not raw_reviews:
            return jsonify({
                "reviews": [],
                "average_rating": 0,
                "counts": counts,
                "total": 0
            }), 200

        for rev in raw_reviews:
            # Lấy dữ liệu từ Dictionary an toàn tuyệt đối
            rating = int(rev.get('rating', 5))
            comment = rev.get('comment', '')
            user_id = rev.get('user_id')
            created_at = rev.get('created_at', '')

            counts[str(rating)] = counts.get(str(rating), 0) + 1
            if comment:
                counts["comment"] += 1
            total_rating += rating

            # Tạm thời gán cứng tên User để loại trừ lỗi import Model
            user_name = "Người dùng OneShop"
            if user_id:
                try:
                    from app.models.user import User
                    user = User.query.get(user_id)
                    if user and user.username:
                        user_name = user.username
                except Exception:
                    user_name = f"Người dùng #{user_id}"

            processed_reviews.append({
                "user_name": user_name,
                "rating": rating,
                "comment": comment,
                "created_at": str(created_at)[:10] if created_at else ""
            })

        avg_rating = round(total_rating / len(raw_reviews), 1)

        return jsonify({
            "reviews": processed_reviews,
            "average_rating": avg_rating,
            "counts": counts,
            "total": len(raw_reviews)
        }), 200

    except Exception as e:
        # IN CHI TIẾT LỖI RA TERMINAL PYTHON ĐỂ DEBUG
        import traceback
        print("\n" + "="*50)
        print("LỖI TẠI GET_REVIEWS:")
        traceback.print_exc()
        print("="*50 + "\n")
        
        return jsonify({"error": str(e)}), 500


@product_bp.route("/products/<int:id>/reviews", methods=["POST"])
def add_review(id: int):
    try:
        if not request.is_json:
            raise ValidationError("Request must be JSON")

        payload = request.get_json() or {}
        fallback_user_id = session.get("user_id") or request.headers.get("X-User-Id")
        dto = ReviewCreateDTO.from_dict(payload, fallback_user_id=fallback_user_id)
        result = ProductService.add_review(id, dto.user_id, dto)
        return jsonify(result), 201
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/products/<int:id>/related", methods=["GET"])
def related_products(id: int):
    try:
        items = ProductService.get_related_products(id)
        return jsonify({"items": items, "total": len(items), "page": 1, "per_page": len(items)}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code

def _get_current_seller_shop_id() -> int:
    user_id = session.get("user_id")
    if not user_id:
        raise ForbiddenError("Login required")

    user = User.query.get(user_id)
    if not user or not user.is_seller:
        raise ForbiddenError("Seller permission required")

    shop = SellerRepository.get_shop_by_owner_id(user.id)
    if not shop:
        raise ForbiddenError("Shop not found")

    return shop.id


@product_bp.route("/product/create", methods=["POST"])
def seller_create_product():
    try:
        if not request.is_json:
            raise ValidationError("Request must be JSON")

        payload = request.get_json() or {}
        dto = SellerProductCreateDTO(
            name=(payload.get("name") or "").strip(),
            description=payload.get("description"),
            price=Decimal(str(payload.get("price", 0))),
            stock=int(payload.get("stock", 0)),
            category_id=payload.get("category_id"),
            images=payload.get("images") or [],
        )
        result = SellerProductService.create(_get_current_seller_shop_id(), dto)
        return jsonify(result), 201
    except (ValueError, TypeError):
        return jsonify({"error": "Dữ liệu đầu vào không hợp lệ"}), 400
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/product/list", methods=["GET"])
def seller_list_products():
    try:
        items = SellerProductService.list_products(_get_current_seller_shop_id())
        return jsonify({"items": items, "total": len(items)}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/product/update", methods=["PUT"])
def seller_update_product():
    try:
        if not request.is_json:
            raise ValidationError("Request must be JSON")
        payload = request.get_json() or {}
        product_id = int(payload.get("product_id", 0))
        dto = SellerProductUpdateDTO(
            product_id=product_id,
            name=payload.get("name"),
            description=payload.get("description"),
            price=Decimal(str(payload["price"])) if payload.get("price") is not None else None,
            stock=int(payload["stock"]) if payload.get("stock") is not None else None,
            category_id=payload.get("category_id"),
        )
        return jsonify(SellerProductService.update(_get_current_seller_shop_id(), dto)), 200
    except (ValueError, TypeError):
        return jsonify({"error": "Dữ liệu đầu vào không hợp lệ"}), 400
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/product/stock", methods=["PUT"])
def seller_update_stock():
    try:
        if not request.is_json:
            raise ValidationError("Request must be JSON")
        payload = request.get_json() or {}
        product_id = int(payload.get("product_id", 0))
        stock = int(payload.get("stock", 0))
        return jsonify(SellerProductService.update_stock(_get_current_seller_shop_id(), product_id, stock)), 200
    except (ValueError, TypeError):
        return jsonify({"error": "Dữ liệu đầu vào không hợp lệ"}), 400
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/product/status", methods=["PUT"])
def seller_update_status():
    try:
        if not request.is_json:
            raise ValidationError("Request must be JSON")
        payload = request.get_json() or {}
        product_id = int(payload.get("product_id", 0))
        status = (payload.get("status") or "").upper()
        return jsonify(SellerProductService.update_status(_get_current_seller_shop_id(), product_id, status)), 200
    except (ValueError, TypeError):
        return jsonify({"error": "Dữ liệu đầu vào không hợp lệ"}), 400
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@product_bp.route("/product", methods=["DELETE"])
def seller_delete_product():
    try:
        if not request.is_json:
            raise ValidationError("Request must be JSON")
        payload = request.get_json() or {}
        product_id = int(payload.get("product_id", 0))
        return jsonify(SellerProductService.soft_delete(_get_current_seller_shop_id(), product_id)), 200
    except (ValueError, TypeError):
        return jsonify({"error": "Dữ liệu đầu vào không hợp lệ"}), 400
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code

@product_bp.route("/products/<int:id>/qr", methods=["GET"])
def get_product_qr(id: int):
    try:
        qr_data = generate_product_qr_by_id(id)
        png_stream = export_qr_png(qr_data)
        return send_file(png_stream, mimetype="image/png")
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code