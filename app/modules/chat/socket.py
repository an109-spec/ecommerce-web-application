from flask import session
from flask_socketio import emit, join_room
from app.extensions.socketio import socketio

online_users = set()


def _current_user_id():
    return session.get("user_id")

@socketio.on("connect")
def on_connect():
    user_id = _current_user_id()
    if user_id:
        online_users.add(user_id)
        emit("user_online", {"user_id": user_id}, broadcast=True)


@socketio.on("disconnect")
def on_disconnect():

    user_id = _current_user_id()
    if user_id:
        online_users.discard(user_id)
        emit("user_offline", {"user_id": user_id}, broadcast=True)


@socketio.on("join_room")
def join_chat(data):
    room_id = data.get("room_id")
    if room_id:
        join_room(f"room_{room_id}")


@socketio.on("send_message")
def relay_message(data):
    room_id = data.get("room_id")
    message = data.get("message") or {}

    if not room_id:
        return

    emit(
        "receive_message",
        message,
        room=f"room_{room_id}",
    )


@socketio.on("seen")
def relay_seen(data):
    room_id = data.get("room_id")
    if not room_id:
        return
    emit(
        "messages_seen",
        {"room_id": room_id},
        room=f"room_{room_id}",
    )