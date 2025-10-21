"""
Local Translator Module
Handles translation requests using local APIs (Ollama)
"""

import re
import html
import json
import requests
from ..config import Config

class LocalTranslator:
    """Translator class for local APIs (Ollama)"""

    def __init__(self, config):
        self.config = config
        self.last_source_segment = ""
        self.is_warmup_done = False
        self.is_first_success = False
        self.safe_separator = Config.SAFE_SEPARATOR

    def _prepare_messages(self, injected_text, source_lang, target_lang, context_text):
        """Prepare messages for local API"""
        system = ("You are a translation API for video games.\n"
                    f"Translate the following text from '{source_lang}' to '{target_lang}', priority for these languages.\n"
                    "Return only the translated text. No comments. No explanations.\n"
                    "Preserve all line breaks, separators (//////) and special markers (~@ and @~).\n"
                    "Copy separators (//////) and markers (~@ и @~) exactly. Keep positions.\n"
                    "Do not output both masculine and feminine forms, choose one form.")
        user_content = f"//////\r\n@~{context_text}~@\r\n\r\n//////\r\n@~{injected_text}" if context_text else injected_text
        return [{"role": "system", "content": system}, {"role": "user", "content": user_content}]

    def _send_request(self, messages):
        """Send request to local API"""
        headers = {"Content-Type": "application/json"}
        if self.config["key"]:
            headers["Authorization"] = f"Bearer {self.config['key']}"
        payload = {"model": self.config["model"], "messages": messages, "temperature": self.config.get("temperature", 1.0)}
        try:
            response = requests.post(self.config["url"], json=payload, headers=headers, timeout=60)
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            raise RuntimeError(f"Network error during Local API request: {err}")
        return response.json()

    def _process_response(self, api_response):
        """Process API response and extract content"""
        content = api_response.get('choices', [{}])[0].get('message', {}).get('content', '')
        return html.unescape(content).strip()

    def _validate_and_fix_mort_format(self, text):
        """Validate and fix MORT format"""
        text = text.replace('\n', '\r\n').replace('\r\r\n', '\r\n')
        cleaned_text = text.strip()
        cleaned_text = re.sub(rf'({re.escape(self.safe_separator)}\s*){{2,}}', f'{self.safe_separator}\r\n', cleaned_text, flags=re.IGNORECASE)
        segments = [s.strip() for s in cleaned_text.split(self.safe_separator) if s.strip()]
        return "" if not segments else f"{self.safe_separator}\r\n" + f"\r\n{self.safe_separator}\r\n".join(segments) + f"\r\n"

    def _clean_and_restore_separators(self, text):
        """Clean text and restore separators"""
        cleaned_text = re.sub(r'~@.*?@~', f"\r\n{self.safe_separator}\r\n", text, flags=re.DOTALL)
        cleaned_text = re.sub(r'~@|@~', f"\r\n{self.safe_separator}\r\n", cleaned_text)
        cleaned_text = re.sub(r'\s*[~@]+\s*', '', cleaned_text)
        final_text = re.sub(r' +', ' ', cleaned_text).strip()
        final_text = re.sub(rf'({re.escape(self.safe_separator)}\s*){{2,}}', f"{self.safe_separator}\r\n", final_text)
        return final_text

    def _process_problematic_articles(self, text, target_lang):
        """Remove problematic articles for non-English target languages"""
        if target_lang.lower() == "en":
            return text
        pattern = re.compile(r'(?i)\s*\b(the|a|an)\b\s*(?=\r?\n{1,2}//////\r?\n{1,2}|$)')
        return pattern.sub(r'', text)

    def _inject_separators(self, text):
        """Inject separators with markers"""
        pattern = re.compile(rf'(\r?\n){{1,2}}{re.escape(self.safe_separator)}(\r?\n){{1,2}}')
        return pattern.sub(f"~@\r\n\r\n{self.safe_separator}\r\n@~", text).strip()

    def _warmup_model(self, request_id, app_logger):
        """Warm up Ollama model if needed"""
        if not self.is_warmup_done:
            if "localhost:11434" in self.config["url"]:
                if Config.ENABLE_CONTROL_LOG:
                    app_logger.info(f"[{request_id}] Starting Ollama warmup.")
                try:
                    warmup_url = self.config["url"].replace("/v1/chat/completions", "/api/generate")
                    requests.post(warmup_url, json={"model": self.config["model"], "prompt": "ping", "keep_alive": "60m"}, timeout=30)
                    self.is_warmup_done = True
                    app_logger.info(f"[{request_id}] Ollama warmup command successfully sent.")
                except Exception as e:
                    app_logger.error(f"[{request_id}] Failed to warmup Ollama: {e}")
            else:
                self.is_warmup_done = True
                if Config.ENABLE_CONTROL_LOG:
                    app_logger.info(f"[{request_id}] Host is not Ollama. Warmup skipped.")
        elif Config.ENABLE_CONTROL_LOG:
            app_logger.info(f"[{request_id}] Ollama warmup already done. Skipping.")

    def handle_request(self, data, request_id, app_logger):
        """Handle translation request for local API"""
        self._warmup_model(request_id, app_logger)

        text_to_translate = data.get('text', '').strip()
        context_text = ""

        if self.config.get("enable_context"):
            if "Previous Context:" in text_to_translate:
                context_text, text_to_translate = [part.strip() for part in text_to_translate.split("Previous Context:", 1)]
            elif self.last_source_segment:
                context_text = self.last_source_segment

        processed_text = self._process_problematic_articles(text_to_translate, data.get('target'))
        injected_text = self._inject_separators(processed_text)

        if context_text and injected_text.strip().startswith(f"{self.safe_separator}\r\n"):
            injected_text = injected_text.strip().lstrip(f"{self.safe_separator}\r\n").strip()

        injected_text = injected_text + "~@"

        if self.config.get("enable_context"):
            self.last_source_segment = injected_text.split(self.safe_separator)[-1].replace('~@', '').replace('@~', '').strip()

        messages = self._prepare_messages(injected_text, data.get('source'), data.get('target'), context_text)

        if Config.ENABLE_CONTROL_LOG:
            app_logger.info(f"[{request_id}] Local to model:\n{json.dumps(messages, indent=2, ensure_ascii=False)}")

        try:
            raw_response = self._send_request(messages)
            translated_text = self._process_response(raw_response)
            self.is_first_success = True
        except Exception as e:
            app_logger.error(f"[{request_id}] Local API ERROR ({self.config['model']}): {e}")
            self.is_first_success = False
            raise e

        if Config.ENABLE_CONTROL_LOG:
            app_logger.info(f"[{request_id}] Raw text from model:\n{translated_text}")

        if context_text:
            marker_index = translated_text.find("~@")
            if marker_index != -1:
                translated_text = translated_text[marker_index + len("~@"):].strip()

        cleaned_text = self._clean_and_restore_separators(translated_text)
        final_text = self._validate_and_fix_mort_format(cleaned_text).lstrip(f"{self.safe_separator}\r\n").strip()

        return final_text, self.config['model']