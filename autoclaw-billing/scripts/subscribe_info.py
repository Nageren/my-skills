#!/usr/bin/env python3
"""Call the AutoClaw subscribe-info endpoint.

Working request:
  POST /agentpay/v1/assistant/subscribe-info
  body: {}

Authentication:
  - Bearer token from --token or local token service
  - X-Auth-* signature: MD5(appId + '&' + timestamp + '&' + appKey)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any


DEFAULT_URL = "https://autoglm-api.zhipuai.cn/agentpay/v1/assistant/subscribe-info"
DEFAULT_TOKEN_URL = "http://127.0.0.1:18432/get_token"
DEFAULT_APP_ID = "100003"
DEFAULT_APP_KEY = "38d2391985e2369a5fb8227d8e6cd5e5"


@dataclass(frozen=True)
class FetchSubscribeInfoRespItem:
    subscribe_id: str
    subscribe_status: str
    product_id: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> FetchSubscribeInfoRespItem:
        return cls(
            subscribe_id=require_str(value, "subscribe_id"),
            subscribe_status=require_str(value, "subscribe_status"),
            product_id=require_str(value, "product_id"),
        )


@dataclass(frozen=True)
class FetchSubscribeInfoResp:
    subscribe_list: list[FetchSubscribeInfoRespItem]
    alipay_first_month_rights: bool
    hit_first_month_exp: bool
    apple_subscribe_status: int

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> FetchSubscribeInfoResp:
        subscribe_items = require_list(value, "subscribe_list")
        return cls(
            subscribe_list=[
                FetchSubscribeInfoRespItem.from_dict(require_dict(item, "subscribe_list item"))
                for item in subscribe_items
            ],
            alipay_first_month_rights=require_bool(value, "alipay_first_month_rights"),
            hit_first_month_exp=require_bool(value, "hit_first_month_exp"),
            apple_subscribe_status=require_int(value, "apple_subscribe_status"),
        )


@dataclass(frozen=True)
class ApiResponse:
    code: int
    msg: str
    time: int
    trace: str
    data: FetchSubscribeInfoResp | None

    @classmethod
    def from_json(cls, raw: str) -> ApiResponse:
        parsed: Any = json.loads(raw)
        root = require_dict(parsed, "response")
        data_value = root.get("data")
        return cls(
            code=require_int(root, "code"),
            msg=require_str(root, "msg"),
            time=require_int(root, "time"),
            trace=require_str(root, "trace"),
            data=None if data_value is None else FetchSubscribeInfoResp.from_dict(require_dict(data_value, "data")),
        )


def require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be an object")
    return value


def require_list(value: dict[str, Any], field: str) -> list[Any]:
    field_value = value.get(field)
    if not isinstance(field_value, list):
        raise TypeError(f"{field} must be a list")
    return field_value


def require_str(value: dict[str, Any], field: str) -> str:
    field_value = value.get(field)
    if not isinstance(field_value, str):
        raise TypeError(f"{field} must be a string")
    return field_value


def require_bool(value: dict[str, Any], field: str) -> bool:
    field_value = value.get(field)
    if not isinstance(field_value, bool):
        raise TypeError(f"{field} must be a bool")
    return field_value


def require_int(value: dict[str, Any], field: str) -> int:
    field_value = value.get(field)
    if isinstance(field_value, bool) or not isinstance(field_value, int):
        raise TypeError(f"{field} must be an int")
    return field_value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Request assistant subscription info.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--token")
    parser.add_argument("--token-url", default=DEFAULT_TOKEN_URL)
    parser.add_argument("--app-id", default=DEFAULT_APP_ID)
    parser.add_argument("--app-key", default=DEFAULT_APP_KEY)
    parser.add_argument("--timestamp", type=int, help="Unix timestamp in seconds. Defaults to now.")
    parser.add_argument("--data", default="{}", help="JSON request body. Defaults to '{}'.")
    parser.add_argument(
        "--bearer-header",
        choices=("Authorization", "Authentication"),
        default="Authorization",
        help="Header used for the Bearer token. Defaults to Authorization.",
    )
    return parser.parse_args()


def build_auth_headers(app_id: str, app_key: str, timestamp: int | None = None) -> dict[str, str]:
    ts = str(timestamp if timestamp is not None else int(time.time()))
    sign_data = f"{app_id}&{ts}&{app_key}"
    sign = hashlib.md5(sign_data.encode("utf-8")).hexdigest()
    return {
        "X-Auth-Appid": app_id,
        "X-Auth-TimeStamp": ts,
        "X-Auth-Sign": sign,
    }


def parse_token_response(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None

    if raw.startswith("Bearer "):
        return raw.removeprefix("Bearer ").strip() or None

    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError:
        return raw

    if isinstance(parsed, str):
        return parsed.strip() or None

    if not isinstance(parsed, dict):
        return None

    for key in ("token", "access_token", "bearer_token"):
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            return value.removeprefix("Bearer ").strip()

    data = parsed.get("data")
    if isinstance(data, dict):
        for key in ("token", "access_token", "bearer_token"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.removeprefix("Bearer ").strip()

    return None


def fetch_bearer_token(token_url: str) -> str:
    request = urllib.request.Request(
        url=token_url,
        headers={"Accept": "application/json, text/plain"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = response.read().decode("utf-8", errors="replace")

    token = parse_token_response(raw)
    if not token:
        raise ValueError(f"token endpoint returned no token: {raw[:200]}")
    return token


def normalize_json_body(raw: str) -> bytes:
    parsed: Any = json.loads(raw)
    return json.dumps(parsed, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def build_request(
    url: str,
    token: str,
    app_id: str,
    app_key: str,
    timestamp: int | None,
    body: bytes,
    bearer_header: str,
) -> urllib.request.Request:
    headers = {
        bearer_header: f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        **build_auth_headers(app_id, app_key, timestamp),
    }
    return urllib.request.Request(url=url, data=body, headers=headers, method="POST")


def main() -> int:
    args = parse_args()
    if not args.app_key:
        print("ERROR: missing app key. Pass --app-key.", file=sys.stderr)
        return 2

    try:
        token = args.token or fetch_bearer_token(args.token_url)
        body = normalize_json_body(args.data)
        request = build_request(
            args.url,
            token,
            args.app_id,
            args.app_key,
            args.timestamp,
            body,
            args.bearer_header,
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            ApiResponse.from_json(response_body)
            print(response_body)
            return 0 if 200 <= response.status < 300 else 1
    except urllib.error.HTTPError as error:
        response_body = error.read().decode("utf-8", errors="replace")
        print(response_body, file=sys.stderr)
        return 1
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
