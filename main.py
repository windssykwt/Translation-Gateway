"""
Translation API Gateway - Main Entry Point
Modular Flask application for handling translation requests via Cloud or Local APIs
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app, log_initial_config, start_background_monitoring

def main():
    """Main entry point for the application"""

    # Create Flask application
    app, cloud_translator = create_app()

    # Log initial configuration
    log_initial_config(app)

    # Start background monitoring for cloud APIs
    start_background_monitoring(cloud_translator, app)

    # Get server configuration
    host = app.config.get('SERVER_HOST', '0.0.0.0')
    port = app.config.get('SERVER_PORT', 5000)
    debug = app.config.get('SERVER_DEBUG', False)

    print(f"Starting Translation API Gateway...")
    print(f"Server running on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print("Press Ctrl+C to stop the server")

    try:
        app.run(
            host=host,
            port=port,
            debug=debug
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)

if __name__ == '__main__':
    main()