from pathlib import Path
from uuid import uuid4

from flask import jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from app.models import User

from . import chat_bp
from .service import ChatService
ALLOWED_CHAT_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

def _current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


@chat_bp.route("/shop/<int:seller_id>")
def open_chat_with_shop(seller_id):
    user = _current_user()
    if not user:
        return redirect(url_for("auth.login", next=url_for("chat.open_chat_with_shop", seller_id=seller_id)))

    room = ChatService.get_or_create_room(
        buyer_id=user.id,
        seller_id=seller_id,
    )
    return redirect(url_for("chat.chat_page", room=room.id))


@chat_bp.route("/<int:seller_id>")
def open_chat_legacy(seller_id):
    return redirect(url_for("chat.open_chat_with_shop", seller_id=seller_id))


@chat_bp.route("")
def chat_page():
    user = _current_user()
    if not user:
        return redirect(url_for("auth.login", next=url_for("chat.chat_page")))

    room_query = request.args.get("room", type=int)
    rooms = ChatService.list_rooms_for_user(user.id)

    active = None
    if room_query:
        active = next((item for item in rooms if item["room"].id == room_query), None)
    if not active and rooms:
        active = rooms[0]

    messages = []
    if active:
        messages = ChatService.get_chat_history(active["room"].id, limit=200)

    return render_template(
        "chat/chat.html",
        rooms=rooms,
        active=active,
        messages=messages,
        current_user=user,
        chat_role="buyer",
    )


@chat_bp.route("/history/<int:room_id>")
def history(room_id):

    user = _current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    room = ChatService.get_room_for_user(room_id, user.id)
    if not room:
        return jsonify({"error": "Forbidden"}), 403
    messages = ChatService.get_chat_history(room_id, limit=200)
    data = [
        {
            "id": message.id,
            "sender_id": message.sender_id,
            "content": message.content,
            "image": message.image,
            "room_id": message.room_id,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }
        for message in messages
    ]

    return jsonify(data)

@chat_bp.route("/send", methods=["POST"])
def send_message():
    user = _current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or request.form

    room_raw = data.get("room_id") if hasattr(data, "get") else None
    try:
        room_id = int(room_raw) if room_raw is not None else None
    except (TypeError, ValueError):
        room_id = None
    content = (data.get("content") or "").strip() if hasattr(data, "get") else ""
    image = (data.get("image") or "").strip() if hasattr(data, "get") else ""

    if not room_id:
        return jsonify({"error": "room_id is required"}), 422
    if not content and not image:
        return jsonify({"error": "content or image is required"}), 422

    room = ChatService.get_room_for_user(room_id, user.id)
    if not room:
        return jsonify({"error": "Forbidden"}), 403

    message = ChatService.create_message_and_notify(
        room_id=room_id,
        sender_id=user.id,
        content=content or None,
        image=image or None,
    )

    if not message:
        return jsonify({"error": "Room not found"}), 404

    return jsonify(
        {
            "id": message.id,
            "room_id": message.room_id,
            "sender_id": message.sender_id,
            "content": message.content,
            "image": message.image,
            "seen": message.seen,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }
    )
@chat_bp.route("/upload-image", methods=["POST"])
def upload_image():
    user = _current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    file = request.files.get("image")
    if file is None or not file.filename:
        return jsonify({"error": "image is required"}), 422

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_CHAT_IMAGE_EXTENSIONS:
        return jsonify({"error": "Định dạng ảnh không hỗ trợ"}), 422

    safe_name = secure_filename(file.filename)
    filename = f"{uuid4().hex}-{safe_name}"
    upload_dir = Path("app/static/uploads/chat")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file.save(upload_dir / filename)

    image_url = url_for("static", filename=f"uploads/chat/{filename}")
    return jsonify({"image": image_url}), 200



@chat_bp.route("/seen/<int:room_id>", methods=["POST"])
def seen_messages(room_id):
    user = _current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    room = ChatService.get_room_for_user(room_id, user.id)
    if not room:
        return jsonify({"error": "Forbidden"}), 403

    ChatService.mark_seen(room_id, user.id)
    return jsonify({"ok": True})