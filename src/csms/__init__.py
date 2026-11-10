"""Community Services Management System Flask application."""

from flask import Flask, jsonify

from csms.config import DevelopmentConfig


def create_app(test_config: dict[str, object] | None = None) -> Flask:
    """Create and configure the CSMS Flask application.

    Args:
        test_config: Optional configuration overrides used during testing.

    Returns:
        A configured Flask application.
    """
    app = Flask(__name__)

    app.config.from_object(DevelopmentConfig)

    if test_config is not None:
        app.config.update(test_config)

    # Health Endpoint - Single source of truth with lowercase status for smoke test compatibility
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(
            {
                "application": app.config.get("APP_SHORT_NAME", "CSMS"),
                "status": "ok",
                "version": app.config.get("APP_VERSION", "1.0.0"),
            }
        ), 200

    # Inject version and app metadata into Jinja2 templates globally
    @app.context_processor
    def inject_app_metadata():
        return {
            "app_name": app.config.get(
                "APP_NAME", "Community Services Management System"
            ),
            "app_short_name": app.config.get("APP_SHORT_NAME", "CSMS"),
            "app_version": app.config.get("APP_VERSION", "1.0.0"),
        }

    from csms.ui.routes import main_blueprint

    app.register_blueprint(main_blueprint)

    return app