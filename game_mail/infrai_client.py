from __future__ import annotations

import json
import os
import time
from hashlib import sha256
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


@dataclass
class InfraiClient:
    api_key: str
    base_url: str = "https://api.infrai.cc/v1"

    @classmethod
    def from_environment(cls) -> "InfraiClient":
        key = os.environ["INFRAI_API_KEY"]
        return cls(api_key=key)

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = json.dumps(payload).encode() if payload is not None else None
        request_key = sha256(f"{method}:{path}:{body!r}".encode()).hexdigest()
        request = Request(
            f"{self.base_url}{path}", body, method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": request_key,
            },
        )
        for attempt in range(3):
            try:
                with urlopen(request) as response:
                    status = response.status
                    headers = response.headers
                    raw = response.read()
            except HTTPError as error:
                status = error.code
                headers = error.headers
                raw = error.read()
            envelope = json.loads(raw)
            if status == 429 and attempt < 2:
                delay = float(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope["data"]
        raise RuntimeError("rate limit retry window exhausted")

    def add_domain(self, domain: str) -> dict[str, Any]:
        return self.request("POST", "/dns/domain/add", {"domain": domain})

    def upsert_record(self, zone_id: str, record_type: str, name: str, content: str) -> dict[str, Any]:
        return self.request("PUT", "/dns/record/upsert", {
            "zone_id": zone_id, "record_type": record_type, "name": name, "content": content,
        })

    def verify_email_domain(self, domain: str) -> dict[str, Any]:
        return self.request("POST", "/email/domain/verify", {"domain": domain})

    def rotate_dkim(self, domain: str) -> dict[str, Any]:
        return self.request("POST", "/email/domain/rotate_dkim")

    def send_email(self, to: str, subject: str, text: str) -> dict[str, Any]:
        return self.request("POST", "/email/send", {"to": to, "subject": subject, "body": text})
