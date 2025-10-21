"""
Translation Routes Module
Handles all translation-related endpoints
"""

import json
import time
import uuid
from flask import request, jsonify
from ..config import Config
from ..translators.cloud_translator import CloudTranslator
from ..translators.local_translator import LocalTranslator

def create_translation_routes(cloud_translator, local_translator, app):
    """Create and register translation routes"""

    @app.route('/translate', methods=['POST'])
    def translate_request():
        """Main translation endpoint"""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        if Config.ENABLE_CONTROL_LOG:
            app.logger.info(f"--- New Request ID: {request_id} ---")

        try:
            data = request.json
            text_to_translate = data.get('text', '').strip()

            if Config.ENABLE_CONTROL_LOG:
                app.logger.info(f"[{request_id}] Incoming JSON: {json.dumps(data, ensure_ascii=False)}")
                app.logger.info(f"[{request_id}] Raw text for translation:\n{text_to_translate}")

            if not text_to_translate:
                return jsonify({"result": "", "errorCode": "400", "errorMessage": "No text to translate."}), 400

            # Process translation based on active mode
            if Config.ACTIVE_MODE == "Cloud":
                translator = cloud_translator
                final_text, api_used = translator.handle_request(data, request_id, app.logger)
                context_log = f"Cloud (Model: {api_used}, History Count: {len(translator.translation_history)})"
            elif Config.ACTIVE_MODE == "Local":
                translator = local_translator
                final_text, api_used = translator.handle_request(data, request_id, app.logger)
                context_log = f"Local (Model: {api_used}, Segment: '{translator.last_source_segment}')"
            else:
                raise ValueError("Invalid ACTIVE_MODE value. Must be 'Cloud' or 'Local'.")

            total_time = time.time() - start_time

            # Log success
            if not translator.is_first_success:
                app.logger.info(f"[{request_id}] ✅ OK. Successful model: **{api_used}**. Time: {total_time:.2f}s.")
                translator.is_first_success = True
            else:
                if Config.ENABLE_CONTROL_LOG:
                    app.logger.info(f"[{request_id}] ✅ OK (Mode: {Config.ACTIVE_MODE}). Used API: {api_used}. Time: {total_time:.2f}s.")

            if Config.ENABLE_CONTROL_LOG:
                app.logger.info(f"[{request_id}] Current internal context: {context_log}")
                app.logger.info(f"[{request_id}] Final text for MORT:\n{final_text}")

            result_array = [final_text]

            final_response_json = {
                "result": result_array,
                "errorCode": "0",
                "errorMessage": ""
            }

            if Config.ENABLE_CONTROL_LOG:
                app.logger.info(f"[{request_id}] Outgoing JSON: {json.dumps(final_response_json, ensure_ascii=False)}")

            return jsonify(final_response_json)

        except Exception as e:
            # Enhanced error logging
            if isinstance(e, RuntimeError):
                app.logger.error(f"[{request_id}] REQUEST PROCESSING ERROR: {e}")
            else:
                app.logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)

            return jsonify({"result": "", "errorCode": "500", "errorMessage": str(e)}), 500

    return app