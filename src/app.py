"""
Flask Application Module
Modular Flask application for handling translation requests
"""

import logging
from flask import Flask
from threading import Thread

from .config import Config
from .translators.cloud_translator import CloudTranslator
from .translators.local_translator import LocalTranslator
from .routes.translation import create_translation_routes
from .routes.health import create_health_routes

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    if not Config.ENABLE_CONTROL_LOG:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    if Config.ENABLE_CONTROL_LOG:
        try:
            file_handler = logging.FileHandler('logs/Log.txt', encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
            app.logger.info("Logging to logs/Log.txt enabled (ENABLE_CONTROL_LOG=True).")
        except PermissionError:
            app.logger.warning("Permission denied to create log file. File logging disabled.")

    # Initialize translators
    cloud_translator = CloudTranslator(
        Config.get_primary_cloud_config(),
        Config.get_secondary_cloud_config()
    )
    local_translator = LocalTranslator(Config.get_local_config())

    # Register routes
    create_translation_routes(cloud_translator, local_translator, app)
    create_health_routes(app)

    return app, cloud_translator

def log_initial_config(app):
    """Log initial configuration"""
    app.logger.info("=" * 60)
    app.logger.info(f"*** API-GATEWAY START: ACTIVE MODE: {Config.ACTIVE_MODE} ***")
    app.logger.info("=" * 60)

    if Config.ACTIVE_MODE == "Cloud":
        primary_config = Config.get_primary_cloud_config()
        secondary_config = Config.get_secondary_cloud_config()

        primary_model = primary_config.get("model", "NONE")
        primary_context = "ON" if primary_config.get("enable_context") else "OFF"
        secondary_model = secondary_config.get("model", "NONE")
        secondary_context = "ON" if secondary_config.get("enable_context") else "OFF"
        has_secondary_key = "Key EXISTS" if secondary_config.get("key") else "No Key"

        app.logger.info(f"Cloud PRIMARY Model: {primary_model} (Context: {primary_context})")
        app.logger.info(f"Cloud SECONDARY Model: {secondary_model} ({has_secondary_key}, Context: {secondary_context})")
    elif Config.ACTIVE_MODE == "Local":
        local_config = Config.get_local_config()
        local_model = local_config.get("model", "NONE")
        local_context = "ON" if local_config.get("enable_context") else "OFF"
        app.logger.info(f"Local (Ollama) Model: {local_model} (Context: {local_context})")

    app.logger.info("=" * 60)

def start_background_monitoring(cloud_translator, app):
    """Start background monitoring for cloud APIs"""
    if Config.ACTIVE_MODE == "Cloud":
        t = Thread(target=cloud_translator._background_check_primary_api, args=(app.logger,))
        t.daemon = True
        t.start()
        return t
    return None