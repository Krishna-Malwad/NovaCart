"""
NovaCart Flask application factory.
"""
import uuid

from flask import Flask, session

from config import Config
from app.database import init_db


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(Config)

    # Make sure DB exists & is seeded before any request is handled
    init_db()

    @app.before_request
    def ensure_session_id():
        if "_id" not in session:
            session["_id"] = str(uuid.uuid4())

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.search import search_bp
    from app.routes.cart import cart_bp
    from app.routes.wishlist import wishlist_bp
    from app.routes.checkout import checkout_bp
    from app.routes.analytics import analytics_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_currency():
        return {"currency": Config.CURRENCY_SYMBOL}

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("404.html"), 404

    return app
