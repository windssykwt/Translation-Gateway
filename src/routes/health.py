"""
Health Check Routes Module
Handles health check and configuration endpoints
"""

from flask import jsonify
from ..config import Config

def create_health_routes(app):
    """Create and register health check routes"""

    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "mode": Config.ACTIVE_MODE,
            "cloud_primary_available": bool(Config.get_primary_cloud_config().get("key")),
            "cloud_secondary_available": bool(Config.get_secondary_cloud_config().get("key"))
        })

    @app.route('/config', methods=['GET'])
    def get_config():
        """Get current configuration (without sensitive data)"""
        return jsonify({
            "active_mode": Config.ACTIVE_MODE,
            "control_log_enabled": Config.ENABLE_CONTROL_LOG,
            "safe_separator": Config.SAFE_SEPARATOR,
            "cloud_primary": {
                "model": Config.get_primary_cloud_config().get("model"),
                "temperature": Config.get_primary_cloud_config().get("temperature"),
                "context_enabled": Config.get_primary_cloud_config().get("enable_context"),
                "has_key": bool(Config.get_primary_cloud_config().get("key"))
            },
            "cloud_secondary": {
                "model": Config.get_secondary_cloud_config().get("model"),
                "temperature": Config.get_secondary_cloud_config().get("temperature"),
                "context_enabled": Config.get_secondary_cloud_config().get("enable_context"),
                "has_key": bool(Config.get_secondary_cloud_config().get("key"))
            },
            "local": {
                "model": Config.get_local_config().get("model"),
                "temperature": Config.get_local_config().get("temperature"),
                "context_enabled": Config.get_local_config().get("enable_context"),
                "url": Config.get_local_config().get("url")
            }
        })

    return app