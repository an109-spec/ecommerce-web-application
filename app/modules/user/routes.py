from pathlib import Path
from uuid import uuid4
from flask import jsonify, render_template, request, session, url_for, redirect
from werkzeug.utils import secure_filename

from app.common.exceptions import AppException

from . import user_bp
from .service import UserService

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

def _resolve_user_id() -> int:
    user_id = session.get("user_id")
    if not user_id:
        raise AppException("Bạn chưa đăng nhập", status_code=401)
    return int(user_id)

@user_bp.route("/center", methods=["GET"])
def user_center_page():
    if not session.get("user_id"):
        return redirect(url_for("auth.login", next=request.url))
    return render_template("user/center.html")


@user_bp.route("/profile", methods=["GET"])
def profile():
    try:
        user_id = _resolve_user_id()
        data = UserService.get_profile(user_id)
        return jsonify(data), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@user_bp.route("/profile", methods=["PATCH"])
def update_profile():
    try:
        user_id = _resolve_user_id()
        payload = request.get_json(silent=True) or {}
        data = UserService.update_profile(user_id, payload)
        return jsonify(data), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code
    
@user_bp.route("/avatar/upload", methods=["POST"])
def upload_avatar():
    try:
        user_id = _resolve_user_id()
        file = request.files.get("avatar")
        if file is None or not file.filename:
            raise AppException("Vui lòng chọn ảnh avatar", status_code=400)

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise AppException("Định dạng ảnh không hỗ trợ", status_code=400)

        safe_name = secure_filename(file.filename)
        filename = f"{uuid4().hex}-{safe_name}"
        upload_dir = Path("app/static/uploads/avatars")
        upload_dir.mkdir(parents=True, exist_ok=True)
        save_path = upload_dir / filename
        file.save(save_path)

        avatar_path = url_for("static", filename=f"uploads/avatars/{filename}")
        avatar_url = UserService.set_avatar_file(user_id, avatar_path)
        return jsonify({"avatar": avatar_url}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@user_bp.route("/avatar", methods=["PATCH"])
def change_avatar():
    try:
        user_id = _resolve_user_id()
        if not request.is_json:
            raise AppException("Request must be JSON", 400)
        payload = request.get_json()
        avatar = payload.get("avatar")
        if not avatar:
            raise AppException("Thiếu avatar URL", 400)
        avatar_url = UserService.change_avatar(user_id, avatar)
        return jsonify({"avatar": avatar_url}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code
    except Exception:
        return jsonify({"error": "Internal Server Error"}), 500


@user_bp.route("/password", methods=["PATCH"])
def change_password():
    try:
        user_id = _resolve_user_id()
        if not request.is_json:
            raise AppException("Request must be JSON", 400)
        payload = request.get_json()
        current_password = payload.get("current_password")
        new_password = payload.get("new_password")
        if not current_password or not new_password:
            raise AppException("Thiếu thông tin mật khẩu", 400)
        if len(new_password) < 8:
            raise AppException("Mật khẩu mới tối thiểu 8 ký tự", 400)
        UserService.change_password(
            user_id=user_id,
            current_password=current_password,
            new_password=new_password,
        )
        return jsonify({"message": "Đổi mật khẩu thành công"}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code
    except Exception:
        return jsonify({"error": "Internal Server Error"}), 500


@user_bp.route("/purchase-history", methods=["GET"])
def purchase_history():
    try:
        user_id = _resolve_user_id()
        history = UserService.purchase_history(user_id)
        return jsonify({"orders": history}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code
    
@user_bp.route("/default-address", methods=["GET"])
def default_address():
    try:
        user_id = _resolve_user_id()
        address = UserService.get_default_address(user_id)
        return jsonify({"address": address}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@user_bp.route("/address", methods=["PUT"])
def update_address():
    try:
        user_id = _resolve_user_id()
        payload = request.get_json(silent=True) or {}
        addresses = UserService.upsert_address(user_id, payload)
        return jsonify({"addresses": addresses}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code



@user_bp.route("/address", methods=["POST"])
def add_address():
    try:
        user_id = _resolve_user_id()
        payload = request.get_json(silent=True) or {}
        addresses = UserService.add_address(user_id, payload)
        return jsonify({"addresses": addresses}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@user_bp.route("/address/<string:address_id>", methods=["DELETE"])
def delete_address(address_id: str):
    try:
        user_id = _resolve_user_id()
        addresses = UserService.delete_address(user_id, address_id)
        return jsonify({"addresses": addresses}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@user_bp.route("/address/<string:address_id>/default", methods=["POST"])
def set_default_address(address_id: str):
    try:
        user_id = _resolve_user_id()
        addresses = UserService.set_default_address(user_id, address_id)
        return jsonify({"addresses": addresses}), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@user_bp.route("/api/provinces", methods=["GET"])
def provinces():
    try:
        data = UserService.list_provinces()
        return jsonify(data), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@user_bp.route("/api/districts", methods=["GET"])
def districts():
    try:
        province_code = (request.args.get("province_code") or "").strip()
        data = UserService.list_districts(province_code)
        return jsonify(data), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


@user_bp.route("/api/wards", methods=["GET"])
def wards():
    try:
        district_code = (request.args.get("district_code") or "").strip()
        data = UserService.list_wards(district_code)
        return jsonify(data), 200
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code