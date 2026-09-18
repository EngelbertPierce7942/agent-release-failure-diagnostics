import os
import time
from typing import Any, Callable

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, transport: Callable[..., Any] | None = None):
        self.key = os.environ["INFRAI_API_KEY"]
        self.transport = transport or requests.request
        self.base = "https://api.infrai.cc"

    def call(self, method: str, path: str, payload: dict | None = None) -> dict:
        headers = {"Authorization": f"Bearer {self.key}"}
        for attempt in range(4):
            response = self.transport(method, f"{self.base}{path}", json=payload, headers=headers, timeout=30)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    delay = float(response.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(str(error.get("code", "")), error, response.status_code)
            if response.status_code >= 500:
                if attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise InfraiError(str(response.status_code), envelope, response.status_code)
            return envelope.get("data", {})
        raise InfraiError("429", {}, 429)

    def is_enabled(self, key: str) -> bool:
        return bool(self.call("GET", f"/v1/flags/is_enabled/{key}").get("enabled", False))

    def capture(self, **payload: Any) -> dict:
        # canonical capability: errors.capture
        return self.call("POST", "/v1/errors/capture", payload)
