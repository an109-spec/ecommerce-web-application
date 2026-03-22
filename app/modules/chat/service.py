from sqlalchemy import and_, func, or_

from app.extensions.db import db
from app.models import Notification, User
from app.models.chat import ChatRoom, Message


class ChatService:

    @staticmethod
    def get_or_create_room(buyer_id, seller_id):

        room = ChatRoom.query.filter_by(
            buyer_id=buyer_id,
            seller_id=seller_id
        ).first()

        if not room:

            room = ChatRoom(
                buyer_id=buyer_id,
                seller_id=seller_id
            )

            db.session.add(room)
            db.session.commit()

        return room

    @staticmethod
    def get_room_for_user(room_id, user_id):
        return (
            ChatRoom.query
            .filter(
                ChatRoom.id == room_id,
                or_(
                    ChatRoom.buyer_id == user_id,
                    ChatRoom.seller_id == user_id,
                )
            )
            .first()
        )

    @staticmethod
    def list_rooms_for_user(user_id, seller_only=False):
        base_query = ChatRoom.query

        if seller_only:
            base_query = base_query.filter(ChatRoom.seller_id == user_id)
        else:
            base_query = base_query.filter(
                or_(ChatRoom.buyer_id == user_id, ChatRoom.seller_id == user_id)
            )

        last_message_subquery = (
            db.session.query(
                Message.room_id,
                func.max(Message.created_at).label("last_message_at")
            )
            .group_by(Message.room_id)
            .subquery()
        )

        rooms = (
            base_query
            .outerjoin(last_message_subquery, last_message_subquery.c.room_id == ChatRoom.id)
            .order_by(
                last_message_subquery.c.last_message_at.desc().nullslast(),
                ChatRoom.created_at.desc(),
            )
            .all()
        )

        room_ids = [room.id for room in rooms]
        last_message_map = {}
        unread_map = {}

        if room_ids:
            latest_messages = (
                db.session.query(Message)
                .join(
                    last_message_subquery,
                    and_(
                        last_message_subquery.c.room_id == Message.room_id,
                        last_message_subquery.c.last_message_at == Message.created_at,
                    )
                )
                .filter(Message.room_id.in_(room_ids))
                .all()
            )
            last_message_map = {message.room_id: message for message in latest_messages}

            unread_rows = (
                db.session.query(Message.room_id, func.count(Message.id))
                .filter(
                    Message.room_id.in_(room_ids),
                    Message.seen.is_(False),
                    Message.sender_id != user_id,
                )
                .group_by(Message.room_id)
                .all()
            )
            unread_map = {room_id: total for room_id, total in unread_rows}

        user_ids = {room.buyer_id for room in rooms} | {room.seller_id for room in rooms}
        users = User.query.filter(User.id.in_(list(user_ids))).all() if user_ids else []
        user_map = {user.id: user for user in users}

        overview = []
        for room in rooms:
            partner_id = room.seller_id if room.buyer_id == user_id else room.buyer_id
            partner = user_map.get(partner_id)
            last_message = last_message_map.get(room.id)

            overview.append({
                "room": room,
                "partner": partner,
                "partner_id": partner_id,
                "last_message": last_message,
                "unread_count": int(unread_map.get(room.id, 0)),
            })

        return overview

    @staticmethod
    def save_message(room_id, sender_id, content=None, image=None):

        msg = Message(
            room_id=room_id,
            sender_id=sender_id,
            content=content,
            image=image,
            seen=False,
        )

        db.session.add(msg)
        db.session.commit()

        return msg

    @staticmethod
    def create_message_and_notify(room_id, sender_id, content=None, image=None):
        room = ChatRoom.query.get(room_id)
        if not room:
            return None

        message = ChatService.save_message(
            room_id=room_id,
            sender_id=sender_id,
            content=content,
            image=image,
        )

        receiver_id = room.seller_id if sender_id == room.buyer_id else room.buyer_id
        notification = Notification(
            user_id=receiver_id,
            title="Tin nhắn mới",
            message=(content or "Bạn nhận được một tin nhắn hình ảnh"),
            is_read=False,
        )
        db.session.add(notification)
        db.session.commit()

        return message
    
    @staticmethod
    def get_chat_history(room_id, limit=50):

        return (
            Message.query
            .filter_by(room_id=room_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .all()
        )


    @staticmethod
    def mark_seen(room_id, user_id):

        messages = (
            Message.query
            .filter(
                Message.room_id == room_id,
                Message.sender_id != user_id,
                Message.seen.is_(False),
            )
            .all()
        )

        for message in messages:
            message.seen = True

        db.session.commit()


    @staticmethod
    def get_unread_count(user_id):

        rooms = ChatRoom.query.filter(
            or_(
                ChatRoom.buyer_id == user_id,
                ChatRoom.seller_id == user_id
            )
        ).all()

        room_ids = [room.id for room in rooms]
        if not room_ids:
            return 0

        return (
            Message.query
            .filter(
                Message.room_id.in_(room_ids),
                Message.sender_id != user_id,
                Message.seen.is_(False),
            )
            .count()
        )