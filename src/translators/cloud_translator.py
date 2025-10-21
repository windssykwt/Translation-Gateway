"""
Cloud Translator Module
Handles translation requests using cloud APIs with auto-switching capabilities
"""

import re
import html
import json
import requests
import time
from threading import Lock
from ..config import Config

class CloudTranslator:
    """Translator class for cloud-based APIs with automatic failover"""

    def __init__(self, primary_config, secondary_config):
        self.primary_api = primary_config
        self.secondary_api = secondary_config
        self.current_api = "PRIMARY"
        self.api_lock = Lock()
        self.translation_history = []
        self.is_first_success = False
        self.safe_separator = Config.SAFE_SEPARATOR

    def _format_history(self):
        """Format translation history for context"""
        if not self.translation_history:
            return ""
        history_str = "\n".join([f"[{i+1}: \"{segment}\"]" for i, segment in enumerate(self.translation_history[-2:])])
        return (
            "\n*** PREVIOUS DIALOG CONTEXT (Target Language): ***\n"
            f"{history_str}\n"
            "*** END OF CONTEXT ***"
        )

    def _prepare_messages_primary(self, text, source_lang, target_lang):
        """Prepare messages for primary API"""
        is_context_enabled = self.primary_api.get("enable_context", False)
        system_prompt = (
            "You are a professional video game localizer and a strict linguistic parser.\n"
            f"Translate the text from '{source_lang}' to '{target_lang}'.\n"
            "CORE DIRECTIVE: Deliver the most accurate literary translation. Prioritize idiomatic and natural expressions, adapting the syntax to ensure the highest stylistic quality and native flow.\n"
            "GENDER PARSING: Analyze gender indicators (pronouns, verbs, adjectives). Use 'PREVIOUS DIALOG CONTEXT' for verification.\n"
            "OUTPUT RULE: Return ONLY the translated text. DO NOT include any commentary, explanations, or introductory text.\n"
            "MANDATORY FORMATTING: MUST preserve all line breaks (\\n) and separators (//////). ABSOLUTELY DO NOT modify the structure."
        )
        if is_context_enabled:
            system_prompt += self._format_history()
        return [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"{text}"}
        ]

    def _prepare_messages_secondary(self, text, source_lang, target_lang):
        """Prepare messages for secondary API"""
        is_context_enabled = self.secondary_api.get("enable_context", False)
        system_prompt = (
            "You are a professional video game localizer and a strict linguistic parser.\n"
            f"Translate the text from '{source_lang}' to '{target_lang}'.\n"
            "CORE DIRECTIVE: Deliver the most accurate literary translation. Prioritize idiomatic and natural expressions, adapting the syntax to ensure the highest stylistic quality и native flow.\n"
            "GENDER PARSING: Analyze gender indicators (pronouns, verbs, adjectives). Use 'PREVIOUS DIALOG CONTEXT' for verification.\n"
            "OUTPUT RULE: Return ONLY the translated text. DO NOT include any commentary, explanations, or introductory text.\n"
            "MANDATORY FORMATTING: MUST preserve all line breaks (\\n) and separators (//////). ABSOLUTELY DO NOT modify the structure."
        )
        if is_context_enabled:
            system_prompt += self._format_history()
        return [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"{text}"}
        ]

    def _send_request(self, api_conf, messages):
        """Send request to API with error handling"""
        headers = {"Content-Type": "application/json"}
        if api_conf["key"]:
            headers["Authorization"] = f"Bearer {api_conf['key']}"
        payload = {"model": api_conf["model"], "messages": messages, "temperature": api_conf.get("temperature", 1.0)}
        try:
            response = requests.post(api_conf["url"], json=payload, headers=headers, timeout=60)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 401:
                raise RuntimeError("Error 401 Unauthorized: Invalid API key.")
            elif status_code == 429:
                raise RuntimeError("Error 429 Too Many Requests: Request limit exceeded.")
            else:
                raise RuntimeError(f"HTTP Error {status_code}: {err}")
        except requests.exceptions.RequestException as err:
            raise RuntimeError(f"Network error during Cloud API request: {err}")
        return response.json()

    def _process_response(self, api_response):
        """Process API response and extract content"""
        content = api_response.get('choices', [{}])[0].get('message', {}).get('content', '')
        return html.unescape(content).strip()

    def _validate_and_fix_mort_format(self, text):
        """Validate and fix MORT format"""
        text = text.replace('\n', '\r\n').replace('\r\r\n', '\r\n')
        cleaned_text = text.strip()
        cleaned_text = re.sub(r'^\s*' + re.escape(self.safe_separator) + r'\s*\r\n', '', cleaned_text)
        cleaned_text = re.sub(r'\r\n\s*' + re.escape(self.safe_separator) + r'\s*$', '', cleaned_text)
        segments = [s.strip() for s in cleaned_text.split(self.safe_separator) if s.strip()]
        return "" if not segments else f"{self.safe_separator}\r\n" + f"\r\n{self.safe_separator}\r\n".join(segments) + f"\r\n"

    def _background_check_primary_api(self, app_logger):
        """Constantly check primary API availability in background"""
        while True:
            time.sleep(60)

            if not self.primary_api.get("key"):
                app_logger.warning("[Background] Cloud 1 API has no key. Constant check stopped.")
                break

            try:
                test_message = [{"role": "user", "content": "hello"}]
                self._send_request(self.primary_api, test_message)

                with self.api_lock:
                    if self.current_api == "SECONDARY":
                        self.current_api = "PRIMARY"
                        app_logger.info("[Background] Cloud 1 API is available again. Switching back to PRIMARY.")
            except Exception as e:
                app_logger.debug(f"[Background] Cloud 1 API is still unavailable: {e}")

    def handle_request(self, data, request_id, app_logger):
        """Handle translation request with auto-switching logic"""
        with self.api_lock:
            active_api_config = self.primary_api if self.current_api == "PRIMARY" else self.secondary_api

        is_context_enabled = active_api_config.get("enable_context", False)

        if not is_context_enabled:
            self.translation_history = []
            if Config.ENABLE_CONTROL_LOG:
                app_logger.info(f"[{request_id}] Dialog Context DISABLED. History reset.")

        text_to_translate = data.get('text', '').strip()
        translated_text = ""
        api_used_name = active_api_config["model"]
        secondary_key_missing = not self.secondary_api.get("key")

        try:
            if Config.ENABLE_CONTROL_LOG:
                app_logger.info(f"[{request_id}] Current dialog history: {self.translation_history}")
                app_logger.info(f"[{request_id}] Sending to {self.current_api} Cloud API.")

            if self.current_api == "PRIMARY":
                messages = self._prepare_messages_primary(text_to_translate, data.get('source'), data.get('target'))
                api_used_name = self.primary_api["model"]
            else:
                messages = self._prepare_messages_secondary(text_to_translate, data.get('source'), data.get('target'))
                api_used_name = self.secondary_api["model"]

            if Config.ENABLE_CONTROL_LOG:
                app_logger.info(f"[{request_id}] Cloud to model:\n{json.dumps(messages, indent=2, ensure_ascii=False)}")

            api_response = self._send_request(active_api_config, messages)
            translated_text = self._process_response(api_response)

        except Exception as e:
            api_current_model = active_api_config["model"]
            self.is_first_success = False

            # Enhanced switching and retry logic
            if self.current_api == "PRIMARY":

                if "Error 401 Unauthorized" in str(e):
                    app_logger.critical(f"[{request_id}] CRITICAL ERROR: Invalid API key for PRIMARY ({api_current_model}) Attempting to switch to backup.")
                else:
                    app_logger.error(f"[{request_id}] PRIMARY API ERROR ({api_current_model}): {e}")

                if secondary_key_missing:
                    app_logger.error(f"[{request_id}] CRITICAL ERROR: Invalid API key for SECONDARY ({self.secondary_api['model']}) Switching IMPOSSIBLE.")
                    raise RuntimeError(f"Primary API unavailable, and backup API not configured: {e}")

                with self.api_lock:
                    self.current_api = "SECONDARY"
                app_logger.info(f"[{request_id}] Auto-switching to backup Cloud 2 API ({self.secondary_api['model']}).")

                # Retry with backup model
                active_api_config = self.secondary_api
                api_model = active_api_config["model"]
                is_context_enabled = active_api_config.get("enable_context", False)

                if not is_context_enabled:
                    self.translation_history = []

                try:
                    messages = self._prepare_messages_secondary(text_to_translate, data.get('source'), data.get('target'))
                    api_response = self._send_request(active_api_config, messages)
                    translated_text = self._process_response(api_response)
                    api_used_name = api_model
                except Exception as secondary_e:
                    raise RuntimeError(f"ERROR: Backup API ({api_model}) is also unavailable. Reason: {secondary_e}")

            else:
                if "Error 401 Unauthorized" in str(e):
                    app_logger.critical(f"[{request_id}] CRITICAL ERROR: Invalid API key for SECONDARY ({api_current_model}).")
                    raise RuntimeError(f"FATAL FAILURE: Invalid API key for backup model.")

                raise RuntimeError(f"SECONDARY API ERROR ({api_current_model}): {e}")

        if Config.ENABLE_CONTROL_LOG:
            app_logger.info(f"[{request_id}] Raw text from model:\n{translated_text}")

        final_translation = translated_text

        # Context logic
        if is_context_enabled:
            self.translation_history = []

            all_translated_segments = [
                s.strip() for s in final_translation.split(self.safe_separator) if s.strip()
            ]
            if all_translated_segments:
                self.translation_history.extend(all_translated_segments)
                if len(self.translation_history) > 2:
                    self.translation_history = self.translation_history[-2:]

                if Config.ENABLE_CONTROL_LOG:
                    app_logger.info(f"[{request_id}] Dialog history updated. Current 2 (or fewer) segments: {self.translation_history}")

        final_text = self._validate_and_fix_mort_format(final_translation).strip()
        return final_text, api_used_name