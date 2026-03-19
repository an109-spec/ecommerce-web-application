import os
from flask import Flask
from datetime import datetime

from app.config import config_by_name
from app.extensions import init_extensions, db
from app.extensions.jwt import jwt
from app.extensions.socketio import socketio
from flask_migrate import Migrate
from flask_mail import Mail
from app.modules.checkout import checkout_bp
from app.modules.auth import auth_bp
from app.modules.product import product_bp
from app.modules.cart import cart_bp
from app.modules.user import user_bp
from app.modules.order import order_bp
from app.modules.payment import payment_bp
from app.modules.chat import chat_bp
from app.modules.admin import admin_bp
from app.modules.audit import audit_bp
from app.modules.promotion import promotion_bp 
from app.modules.home import home_bp
from app.modules.seller import seller_bp

from app.cli import register_cli

mail = Mail()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    env = os.getenv("FLASK_ENV", "development")
    config_class = config_by_name.get(env)

    if not config_class:
        raise RuntimeError(f"Invalid environment: {env}")

    app.config.from_object(config_class)

    # Init extensions
    init_extensions(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Dev auto create tables (SQLite only)
    if env == "development" and app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        with app.app_context():
            from app import models
            db.create_all()

    # Register blueprints
    register_blueprints(app)
    register_cli(app)

    @app.context_processor
    def inject_globals():
        from flask import session
        from app.models import User, Shop

        current_user = None
        current_shop = None
        user_id = session.get("user_id")

        if user_id:
            current_user = User.query.get(user_id)
            if current_user:
                current_shop = Shop.query.filter_by(owner_id=current_user.id).first()

        return {
            "current_year": datetime.now().year,
            "current_user": current_user,
            "current_shop": current_shop,
        }

    if app.config["DEBUG"]:
        print("DB URI:", app.config["SQLALCHEMY_DATABASE_URI"])
        print(app.url_map)

    return app


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(promotion_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(seller_bp)