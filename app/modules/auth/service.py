from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from app.common.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.extensions import db
from app.models import User, UserProfile, user
from app.models.otp import OTPCode

from app.common.security.otp import get_otp_expired_at

from .dto import (
    LoginDTO,
    RegisterDTO,
    RequestPasswordResetDTO,
    ResetPasswordDTO,
    RequestPasswordResetResultDTO,
)

from .otp_service import OTPService
from .sms_service import SMSService
from .mail_service import MailService
from flask_mail import Message
from app.extensions.mail import mail
from .email_service import EmailService
logger = logging.getLogger(__name__)
class AuthService:

    # ======================================================
    # UTIL
    # ======================================================
    @staticmethod
    def send_otp_email(email, otp_code):
        msg = Message(
            subject="Your OTP Code",
            recipients=[email],
            body=f"Your OTP is: {otp_code}"
        )
        mail.send(msg)
    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        if not identifier or not identifier.strip():
            raise ValidationError("Thiếu email hoặc số điện thoại")

        identifier = identifier.strip()

        # Nếu là email thì lower
        if "@" in identifier:
            return identifier.lower()

         # Phone normalize (bỏ khoảng trắng/dấu gạch/dấu chấm)
        return AuthService._normalize_phone(identifier)

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        phone = phone.strip()
        phone = phone.replace(" ", "").replace("-", "").replace(".", "")
        return phone

    @staticmethod
    def _get_user_by_identifier(identifier: str) -> User | None:
        return User.query.filter(
            or_(
                User.email == identifier,
                User.phone == identifier,
            )
        ).first()

    @staticmethod
    def _generate_username(email: str | None, phone: str | None) -> str:
        """Sinh username từ email/phone và tự xử lý trùng."""
        if email:
            base_username = email.split("@", 1)[0].strip().lower()
        elif phone:
            base_username = phone.strip()
        else:
            raise ValidationError("Phải cung cấp email hoặc số điện thoại")

        if not base_username:
            raise ValidationError("Không thể tạo username hợp lệ")

        candidate = base_username
        suffix = 1

        while User.query.filter_by(username=candidate).first() is not None:
            candidate = f"{base_username}{suffix}"
            suffix += 1

        return candidate

    # ======================================================
    # REGISTER
    # ======================================================

    @staticmethod
    def register(dto: RegisterDTO) -> User:
        if not dto.email and not dto.phone:
            raise ValidationError("Phải cung cấp email hoặc số điện thoại")

        if not dto.full_name or not dto.full_name.strip():
            raise ValidationError("Thiếu họ tên")

        email = dto.email.lower().strip() if dto.email else None
        phone = AuthService._normalize_phone(dto.phone) if dto.phone else None

        # Model hiện tại yêu cầu email non-null. Nếu user đăng ký bằng phone,
        # tạo một email nội bộ để đảm bảo insert không lỗi.
        if not email and phone:
            email = f"{phone}@phone.local"

        user = User(
            username=AuthService._generate_username(email, phone),
            email=email,
            phone=phone,
            password_hash=generate_password_hash(dto.password),
        )

        profile = UserProfile(full_name=dto.full_name.strip())

        try:
            db.session.add(user)
            db.session.flush()

            profile.user_id = user.id
            db.session.add(profile)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError("Email, số điện thoại hoặc username đã tồn tại")

        return user

    # ======================================================
    # LOGIN
    # ======================================================

    @staticmethod
    def login(dto: LoginDTO) -> User:
        identifier = AuthService._normalize_identifier(dto.identifier)
        user = AuthService._get_user_by_identifier(identifier)

        # Không tiết lộ user tồn tại
        if not user:
            raise UnauthorizedError("Sai thông tin đăng nhập")

        now = datetime.now(timezone.utc)

        # ===== Check lock =====
        if user.locked_until and user.locked_until > now:
            raise UnauthorizedError(
                message="Tài khoản bị khóa",
                locked_until=user.locked_until,
            )
        if user.is_banned:
            raise UnauthorizedError("Tài khoản của bạn đã bị khóa. Liên hệ admin để mở khóa")

        # ===== Check password =====
        if not check_password_hash(user.password_hash, dto.password):
            user.failed_login_attempts += 1
            user.last_failed_login = now

            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=15)

            db.session.commit()
            raise UnauthorizedError("Sai thông tin đăng nhập")

        # ===== Login success =====
        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()

        from app.modules.cart.service import CartService 
        CartService.load_cart_from_db(user.id)
        
        return user

    # ======================================================
    # REQUEST PASSWORD RESET
    # ======================================================
    def request_password_reset(dto: RequestPasswordResetDTO) -> RequestPasswordResetResultDTO:
        identifier = AuthService._normalize_identifier(dto.identifier)
        user = AuthService._get_user_by_identifier(identifier)

        expires_at = get_otp_expired_at()

        # Không tiết lộ user tồn tại
        if not user:
            logger.info("Password reset requested for non-existing identifier")
            return RequestPasswordResetResultDTO(
                otp_expires_at_iso=expires_at.isoformat(),
                delivery_channel="email",
                otp_preview=None,
            )

        is_internal_phone_email = bool(user.email and user.email.endswith("@phone.local"))
        # Chỉ gửi OTP qua email thật
        if user.email and not is_internal_phone_email:
            email_code = OTPService.create_otp(user, otp_type="email")
            try:
                EmailService.send_otp(user.email, email_code)
                logger.info("Password reset OTP sent via email for user_id=%s", user.id)
            except Exception as exc:
                logger.exception("Failed to send OTP email for user_id=%s: %s", user.id, exc)
            return RequestPasswordResetResultDTO(
                otp_expires_at_iso=expires_at.isoformat(),
                delivery_channel="email",
                otp_preview=None,
            )
        logger.warning("User has no valid email for OTP delivery. user_id=%s", user.id)
        return RequestPasswordResetResultDTO(
            otp_expires_at_iso=expires_at.isoformat(),
            delivery_channel="email",
            otp_preview=None,
        )

    # ======================================================
    # RESET PASSWORD
    # ======================================================

    @staticmethod
    def reset_password(dto: ResetPasswordDTO) -> None:
        identifier = AuthService._normalize_identifier(dto.identifier)
        user = AuthService._get_user_by_identifier(identifier)

        if not user:
            raise UnauthorizedError("OTP không hợp lệ")

        if dto.otp_type not in ("email", "sms"):
            raise ValidationError("Loại OTP không hợp lệ")

        is_valid = OTPService.verify_otp(
            user_id=user.id,
            code=dto.otp_code,
            otp_type=dto.otp_type,
        )

        if not is_valid:
            raise UnauthorizedError("OTP không hợp lệ hoặc đã hết hạn")

        if len(dto.new_password) < 8:
            raise ConflictError("Mật khẩu phải tối thiểu 8 ký tự")

        if check_password_hash(user.password_hash, dto.new_password):
            raise ConflictError("Mật khẩu mới không được trùng mật khẩu cũ")

        try:
            user.password_hash = generate_password_hash(dto.new_password)
            user.failed_login_attempts = 0
            user.locked_until = None

            OTPCode.query.filter(
                OTPCode.user_id == user.id,
                OTPCode.type.in_(("email", "sms"))
            ).delete()

            db.session.commit()   # ← BẮT BUỘC

        except Exception as e:
            db.session.rollback()
            raise RuntimeError("Không thể cập nhật mật khẩu") from e