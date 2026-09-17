import json
import requests
from typing import List, Dict, Any, Optional
from app.ai.base_provider import BaseAIProvider

class GroqProvider(BaseAIProvider):
    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        super().__init__(model_name)
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def provider_name(self) -> str:
        return "groq"

    def health_check(self) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "provider": self.provider_name,
                "model": self.model_name,
                "status": "unconfigured",
                "message": "GROQ_API_KEY is not set."
            }
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "status": "ready",
            "message": "Groq API key configured."
        }

    def complete(self, messages: List[Dict[str, str]], system_prompt: str, response_format_json: bool = True) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "raw_content": "",
                "parsed_json": None,
                "provider": self.provider_name,
                "model": self.model_name,
                "success": False,
                "error": "GROQ_API_KEY not configured."
            }

        formatted = [{"role": "system", "content": system_prompt}]
        for m in messages:
            role = "assistant" if (m.get("role") or m.get("sender")) in ("agent", "assistant") else "user"
            content = m.get("content") or m.get("message") or ""
            formatted.append({"role": role, "content": content})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": formatted,
            "temperature": 0.1
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            resp = requests.post(self.url, headers=headers, json=payload, timeout=12)
            if resp.status_code != 200:
                return {
                    "raw_content": "",
                    "parsed_json": None,
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "success": False,
                    "error": f"Groq HTTP {resp.status_code}: {resp.text[:200]}"
                }

            data = resp.json()
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")

            parsed_json = None
            if response_format_json and content:
                try:
                    parsed_json = json.loads(content)
                except Exception:
                    # Clean markdown code blocks if any
                    c = content.strip()
                    if c.startswith("```json"):
                        c = c[7:]
                    if c.startswith("```"):
                        c = c[3:]
                    if c.endswith("```"):
                        c = c[:-3]
                    try:
                        parsed_json = json.loads(c.strip())
                    except Exception:
                        parsed_json = None

            return {
                "raw_content": content,
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
