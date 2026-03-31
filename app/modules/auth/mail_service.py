import logging
from flask import current_app
from flask_mail import Message
from app.extensions import mail
from app.common.exceptions import ValidationError

logger = logging.getLogger(__name__)


class MailService:

    @staticmethod
    def send_otp_email(to_email: str, otp_code: str) -> None:
        if not to_email or "@" not in to_email:
            raise ValidationError("Email không hợp lệ")

        try:
            # ===== DEVELOPMENT =====
            if current_app.config["ENV"] == "development" or current_app.config.get("DEBUG"):
                logger.info(f"[DEV EMAIL] To: {to_email} | OTP: {otp_code}")
                return
            sender_mail = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
            if not sender_mail:
                logger.error("MAIL_USERNAME hoặc MAIL_DEFAULT_SENDER chưa được cấu hình!")
                raise RuntimeError("Cấu hình gửi mail chưa hoàn thiện")
            # ===== PRODUCTION =====
# ===== PRODUCTION =====
            msg = Message(
                subject="Mã OTP đặt lại mật khẩu",
                recipients=[to_email],
                # Sửa dòng này để lấy email của bạn làm mặc định nếu config bị trống
                sender=current_app.config.get("MAIL_DEFAULT_SENDER") or "annduyy85@gmail.com"
            )

            msg.body = (
                f"Mã OTP của bạn là: {otp_code}\n\n"
                "Mã có hiệu lực trong 5 phút.\n"
                "Nếu bạn không yêu cầu, vui lòng bỏ qua email này."
            )

            mail.send(msg)

        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            raise RuntimeError("Không thể gửi email")