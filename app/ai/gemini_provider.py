import json
import requests
from typing import List, Dict, Any, Optional
from app.ai.base_provider import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini"

    def health_check(self) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "provider": self.provider_name,
                "model": self.model_name,
                "status": "unconfigured",
                "message": "GEMINI_API_KEY is not set."
            }
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "status": "ready",
            "message": "Gemini API key configured."
        }

    def complete(self, messages: List[Dict[str, str]], system_prompt: str, response_format_json: bool = True) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "raw_content": "",
                "parsed_json": None,
                "provider": self.provider_name,
                "model": self.model_name,
                "success": False,
                "error": "GEMINI_API_KEY not configured."
            }

        url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
        
        # Build contents
        contents = []
        # Add system prompt as initial turn
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will strictly follow all system policies and instructions."}]
            })

        for m in messages:
            role = m.get("role") or m.get("sender")
            if role in ("agent", "assistant", "model"):
                g_role = "model"
            else:
                g_role = "user"
            text = m.get("content") or m.get("message") or ""
            contents.append({
                "role": g_role,
                "parts": [{"text": text}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.1,
            }
        }
        if response_format_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code != 200:
                return {
                    "raw_content": "",
                    "parsed_json": None,
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "success": False,
                    "error": f"Gemini HTTP {resp.status_code}: {resp.text[:200]}"
                }

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return {
                    "raw_content": "",
                    "parsed_json": None,
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "success": False,
                    "error": "No candidates returned by Gemini"
                }

            text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            parsed_json = None
            if response_format_json and text_content:
                try:
                    parsed_json = json.loads(text_content)
                except Exception:
                    # Clean possible markdown fence
                    cleaned = text_content.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    if cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    try:
                        parsed_json = json.loads(cleaned.strip())
                    except Exception:
                        parsed_json = None

            return {
                "raw_content": text_content,
                "parsed_json": parsed_json,
                "provider": self.provider_name,
                "model": self.model_name,
                "success": True,
                "error": None
            }

        except Exception as e:
            return {
                "raw_content": "",
                "parsed_json": None,
                "provider": self.provider_name,
                "model": self.model_name,
                "success": False,
                "error": str(e)
            }
