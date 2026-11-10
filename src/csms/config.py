"""Configuration settings for the CSMS Flask application."""

import os


class BaseConfig:
    """Settings shared by all application environments."""

    APP_NAME = "Community Services Management System"
    APP_SHORT_NAME = "CSMS"
    APP_VERSION = "1.0.0"
    CURRENT_SPRINT = "Sprint 6 - Final Release"

    SECRET_KEY = os.environ.get(
        "CSMS_SECRET_KEY",
        "development-only-secret-key",
    )


class DevelopmentConfig(BaseConfig):
    """Local development configuration."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Automated testing configuration."""

    TESTING = True
    DEBUG = False
    SECRET_KEY = "testing-secret-key"
    APP_VERSION = "0.1.0"