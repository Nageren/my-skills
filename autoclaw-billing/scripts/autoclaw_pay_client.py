#!/usr/bin/env python3
"""Client helpers for AutoClaw payment product APIs.

This module keeps request signing, token fetching, HTTP transport, and response
normalization in one place so skill workflows do not duplicate fragile request
logic.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://autoglm-api.zhipuai.cn"
DEFAULT_TOKEN_URL = "http://127.0.0.1:18432/get_token"
DEFAULT_APP_ID = "100003"
DEFAULT_APP_KEY = "38d2391985e2369a5fb8227d8e6cd5e5"
SKILL_ROOT = Path(__file__).resolve().parents[1]
VENDOR_DIR = SKILL_ROOT / ".vendor"
POSIX_OPENCLAW_TMP_DIR = Path("/tmp/openclaw")
OPENCLAW_TMP_DIR_NAME = "openclaw"
QR_OUTPUT_RELATIVE_DIR = Path("autoclaw-billing") / "qrcode"
TMP_DIR_ACCESS_MODE = os.W_OK | os.X_OK
QR_CLEANUP_LOCK_NAME = ".qr-cleanup.lock"
QR_CLEANUP_MARKER_NAME = ".qr-cleanup.marker"
QR_TTL_SECONDS = 30 * 60
QR_CLEANUP_INTERVAL_SECONDS = 60
QR_CLEANUP_LOCK_STALE_SECONDS = 5 * 60
QR_CLEANUP_MAX_DELETE = 100
QR_CLEANUP_BUDGET_SECONDS = 0.1
QR_REPLACED_FILE_GRACE_SECONDS = 20

PRODUCT_INFO_PATH = "/agentpay/v1/assistant/alipay-product-info"
SUBSCRIBE_INFO_PATH = "/agentpay/v1/assistant/subscribe-info"
CREATE_ONETIME_PATH = "/agentpay/v1/assistant/create-onetime-agent"
CREATE_SUBSCRIBE_PATH = "/agentpay/v1/assistant/create-subscribe-agent"
MOCK_CREATE_PRODUCT_ORDER_PROXY_URL = "http://127.0.0.1:8000/tools/create_product_order"
DEFAULT_CREATE_ONETIME_TRANSPORT = "alipay-bot-proxy"
MOCK_CREATE_ONETIME_TRANSPORT = "mock"
CREATE_ONETIME_TRANSPORTS = (DEFAULT_CREATE_ONETIME_TRANSPORT, MOCK_CREATE_ONETIME_TRANSPORT)
ALIPAY_PAYMENT_SKILL_NAME = "alipay-payment-skill"
DEFAULT_ALIPAY_BOT_BIN = "alipay-bot"
SELLER_NAME = "北京智谱华章科技股份有限公司"
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
URL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z\d+.-]*:")
WINDOWS_DRIVE_PATH_RE = re.compile(r"^[a-zA-Z]:[\\/]")
WINDOWS_UNC_PATH_RE = re.compile(r"^\\\\[^\\]+\\[^\\]+")
OMITTED_FROM_MODEL_OUTPUT = object()
INACTIVE_SUBSCRIBE_STATUSES = {
    "cancel",
    "canceled",
    "cancelled",
    "closed",
    "expired",
    "failed",
    "terminated",
    "unsubscribe",
    "unsubscribed",
}
SUBSCRIBE_VALIDITY_FIELDS = (
    "period_day",
    "valid_until",
    "valid_to",
    "expire_time",
    "expire_at",
    "end_time",
    "next_billing_time",
    "subscribe_end_time",
)


class AutoClawPayError(RuntimeError):
    """Raised when request preparation, transport, or response parsing fails."""


def resolve_alipay_bot_bin() -> str | None:
    """Return an executable alipay-bot path that subprocess can launch."""
    names = [DEFAULT_ALIPAY_BOT_BIN]
    if os.name == "nt":
        names = ["alipay-bot.cmd", "alipay-bot.exe", DEFAULT_ALIPAY_BOT_BIN]

    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved

    for path in bundled_alipay_bot_candidates(names):
        if path.exists():
            return str(path)

    return None


def bundled_alipay_bot_candidates(names: list[str]) -> list[Path]:
    """Find AutoClaw's bundled node tool next to the bundled Python runtime."""
    candidates: list[Path] = []
    try:
        executable = Path(sys.executable).resolve()
    except OSError:
        return candidates

    for parent in executable.parents:
        for node_dir in (parent / "node", parent / "resources" / "node"):
            for name in names:
                candidates.append(node_dir / name)
    return candidates


def run_alipay_bot_command(
    command: list[str],
    *,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    """Run alipay-bot, using cmd.exe-compatible quoting for Windows npm shims."""
    use_windows_shell = (
        os.name == "nt"
        and bool(command)
        and command[0].lower().endswith((".cmd", ".bat"))
    )
    args: list[str] | str = (
        subprocess.list2cmdline(command) if use_windows_shell else command
    )
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=use_windows_shell,
    )


@dataclass(frozen=True)
class ClientConfig:
    app_id: str
    app_key: str
    base_url: str = DEFAULT_BASE_URL
    token_url: str = DEFAULT_TOKEN_URL
    token: str | None = None
    cookie: str | None = None
    timestamp: int | None = None
    timeout: int = 30
    create_onetime_transport: str = DEFAULT_CREATE_ONETIME_TRANSPORT


@dataclass(frozen=True)
class TokenContext:
    token: str
    cookie: str | None = None


class CreateOnetimeOrderRequester(ABC):
    """Transport abstraction for credit-pack one-time order creation."""

    @abstractmethod
    def create_order(
        self,
        payload: dict[str, Any],
        *,
        session_id: str | None,
        headers: dict[str, str],
        config: ClientConfig,
    ) -> dict[str, Any]:
        """Submit the create-onetime payload and return the raw API response."""


class AlipayBotProxyCreateOnetimeOrderRequester(CreateOnetimeOrderRequester):
    """Requester backed by `alipay-bot proxy-trade-request http`."""

    def target_url(self, config: ClientConfig) -> str:
        return join_url(config.base_url, CREATE_ONETIME_PATH)

    def create_order(
        self,
        payload: dict[str, Any],
        *,
        session_id: str | None,
        headers: dict[str, str],
        config: ClientConfig,
    ) -> dict[str, Any]:
        session = require_text(session_id, "session_id")
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        timeout_ms = min(max(config.timeout * 1000, 100), 60000)
        alipay_bot_bin = resolve_alipay_bot_bin()
        if not alipay_bot_bin:
            raise AutoClawPayError(
                "alipay-bot executable not found. Install alipay-bot or ensure "
                "AutoClaw's bundled node directory is available."
            )
        command = [
            alipay_bot_bin,
            "proxy-trade-request",
            "http",
            "--url",
            self.target_url(config),
            "-X",
            "POST",
            "-d",
            body,
            "--session-id",
            session,
            "--timeout-ms",
            str(timeout_ms),
        ]
        for key, value in headers.items():
            command.extend(["-H", f"{key}:{value}"])
        try:
            completed = run_alipay_bot_command(
                command,
                timeout=config.timeout + 5,
            )
        except Exception as error:
            raise AutoClawPayError(f"proxy-trade-request failed: {error}") from error

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        if completed.returncode != 0:
            raise AutoClawPayError(
                "proxy-trade-request failed: "
                f"returncode={completed.returncode}, stdout={stdout[:1000]}, stderr={stderr[:1000]}"
            )
        return parse_proxy_stdout_json(stdout)


class MockCreateOnetimeOrderRequester(AlipayBotProxyCreateOnetimeOrderRequester):
    """Mock requester backed by proxy-trade-request with a local target URL."""

    def target_url(self, config: ClientConfig) -> str:
        _ = config
        return MOCK_CREATE_PRODUCT_ORDER_PROXY_URL


def build_create_onetime_order_requester(name: str) -> CreateOnetimeOrderRequester:
    transport = name.strip().lower()
    if transport == DEFAULT_CREATE_ONETIME_TRANSPORT:
        return AlipayBotProxyCreateOnetimeOrderRequester()
    if transport == MOCK_CREATE_ONETIME_TRANSPORT:
        return MockCreateOnetimeOrderRequester()
    raise AutoClawPayError(
        "unknown create-onetime transport "
        f"{name!r}; expected one of: {', '.join(CREATE_ONETIME_TRANSPORTS)}"
    )


class AutoClawPayClient:
    def __init__(self, config: ClientConfig):
        if not config.app_id.strip():
            raise AutoClawPayError("app_id must be a non-empty string")
        if not config.app_key.strip():
            raise AutoClawPayError("app_key must be a non-empty string")
        self.config = config
        self.create_onetime_order_requester = build_create_onetime_order_requester(
            config.create_onetime_transport
        )

    def product_info(self) -> dict[str, Any]:
        response = self._post(PRODUCT_INFO_PATH, {})
        return normalize_product_info_response(response)

    def subscribe_info(self) -> dict[str, Any]:
        response = self._post(SUBSCRIBE_INFO_PATH, {})
        return normalize_subscribe_info_response(response)

    def member_list(self) -> dict[str, Any]:
        return build_member_list_view(self.product_info(), self.subscribe_info())

    def create_onetime(self, product_id: str, session_id: str | None = None) -> dict[str, Any]:
        product_id = require_text(product_id, "product_id")
        response = self._post_create_onetime({"product_id": product_id}, session_id=session_id)
        return normalize_create_onetime_response(response)

    def create_subscribe(self, source_id: str, product_id: str) -> dict[str, Any]:
        source_id = require_text(source_id, "source_id")
        product_id = require_text(product_id, "product_id")
        response = self._post(
            CREATE_SUBSCRIBE_PATH,
            {
                "source_id": source_id,
                "product_id": product_id,
            },
        )
        return normalize_create_subscribe_response(response)

    def raw_product_info(self) -> dict[str, Any]:
        return self._post(PRODUCT_INFO_PATH, {})

    def raw_subscribe_info(self) -> dict[str, Any]:
        return self._post(SUBSCRIBE_INFO_PATH, {})

    def raw_create_onetime(self, product_id: str, session_id: str | None = None) -> dict[str, Any]:
        return self._post_create_onetime({"product_id": require_text(product_id, "product_id")}, session_id=session_id)

    def raw_create_subscribe(self, source_id: str, product_id: str) -> dict[str, Any]:
        return self._post(
            CREATE_SUBSCRIBE_PATH,
            {
                "source_id": require_text(source_id, "source_id"),
                "product_id": require_text(product_id, "product_id"),
            },
        )

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        token_context = self._resolve_token_context()
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            url=join_url(self.config.base_url, path),
            data=body,
            headers=self._build_headers(token_context),
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            raw = error.read().decode("utf-8", errors="replace")
            raise AutoClawPayError(f"HTTP {error.code}: {raw}") from error
        except urllib.error.URLError as error:
            raise AutoClawPayError(f"request failed: {error}") from error

        return parse_json_object(raw, "API response")

    def _post_create_onetime(self, payload: dict[str, Any], *, session_id: str | None) -> dict[str, Any]:
        token_context = self._resolve_token_context()
        headers = self._build_headers(token_context)
        return self.create_onetime_order_requester.create_order(
            payload,
            session_id=session_id,
            headers=headers,
            config=self.config,
        )

    def _build_headers(self, token_context: TokenContext) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {token_context.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            **build_auth_headers(self.config.app_id, self.config.app_key, self.config.timestamp),
        }
        cookie = self.config.cookie or token_context.cookie
        if cookie:
            headers["Cookie"] = cookie
        return headers

    def _resolve_token_context(self) -> TokenContext:
        if self.config.token:
            return TokenContext(token=strip_bearer_prefix(self.config.token))
        return fetch_token_context(self.config.token_url, self.config.timeout)


def build_auth_headers(app_id: str, app_key: str, timestamp: int | None = None) -> dict[str, str]:
    ts = str(timestamp if timestamp is not None else int(time.time()))
    sign_data = f"{app_id}&{ts}&{app_key}"
    return {
        "X-Auth-Appid": app_id,
        "X-Auth-TimeStamp": ts,
        "X-Auth-Sign": hashlib.md5(sign_data.encode("utf-8")).hexdigest(),
    }


def fetch_token_context(token_url: str, timeout: int) -> TokenContext:
    request = urllib.request.Request(
        url=token_url,
        headers={"Accept": "application/json, text/plain"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace").strip()
    except urllib.error.URLError as error:
        raise AutoClawPayError(f"failed to fetch bearer token: {error}") from error

    context = parse_token_response(raw)
    if not context:
        raise AutoClawPayError(f"token endpoint returned no token: {raw[:200]}")
    return context


def parse_token_response(raw: str) -> TokenContext | None:
    raw = raw.strip()
    if not raw:
        return None

    if raw.startswith("Bearer "):
        return TokenContext(token=strip_bearer_prefix(raw))

    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError:
        return TokenContext(token=raw)

    if isinstance(parsed, str):
        token = parsed.strip()
        return TokenContext(token=strip_bearer_prefix(token)) if token else None

    if not isinstance(parsed, dict):
        return None

    token = extract_token(parsed)
    cookie = extract_string(parsed, "cookie")
    data = parsed.get("data")
    if isinstance(data, dict):
        token = token or extract_token(data)
        cookie = cookie or extract_string(data, "cookie")

    return TokenContext(token=token, cookie=cookie) if token else None


def normalize_product_info_response(response: dict[str, Any]) -> dict[str, Any]:
    ensure_success_response(response)
    data = require_object(response.get("data"), "data")
    member_list = require_list(data.get("member_list"), "data.member_list")
    boost_list = require_list(data.get("boost_list"), "data.boost_list")
    return {
        "success": True,
        "code": response.get("code"),
        "msg": response.get("msg"),
        "trace": response.get("trace"),
        "member_list": [normalize_product(item) for item in member_list],
        "boost_list": [normalize_product(item) for item in boost_list],
        "hit_boost_product_day_limit": data.get("hit_boost_product_day_limit"),
    }


def normalize_subscribe_info_response(response: dict[str, Any]) -> dict[str, Any]:
    ensure_success_response(response)
    data = require_object(response.get("data"), "data")
    subscribe_list = require_list(data.get("subscribe_list"), "data.subscribe_list")
    normalized_subscribe_list = [normalize_subscribe_info_item(item) for item in subscribe_list]
    current_subscribe_list = [
        item for item in normalized_subscribe_list if is_current_subscribe_item(item)
    ]
    alipay_first_month_rights = require_bool(
        data.get("alipay_first_month_rights"),
        "data.alipay_first_month_rights",
    )
    hit_first_month_exp = require_bool(
        data.get("hit_first_month_exp"),
        "data.hit_first_month_exp",
    )
    return {
        "success": True,
        "code": response.get("code"),
        "msg": response.get("msg"),
        "trace": response.get("trace"),
        "subscribe_list": normalized_subscribe_list,
        "current_subscribe_list": current_subscribe_list,
        "current_subscribed_product_ids": [
            item["product_id"] for item in current_subscribe_list
        ],
        "alipay_first_month_rights": alipay_first_month_rights,
        "hit_first_month_exp": hit_first_month_exp,
        "show_first_month_price": (
            hit_first_month_exp
            and not subscribe_list
            and alipay_first_month_rights
        ),
        "apple_subscribe_status": require_int(
            data.get("apple_subscribe_status"),
            "data.apple_subscribe_status",
        ),
    }


def build_member_list_view(
    product_info: dict[str, Any],
    subscribe_info: dict[str, Any],
) -> dict[str, Any]:
    member_list = require_list(product_info.get("member_list"), "member_list")
    current_subscribe_list = require_list(
        subscribe_info.get("current_subscribe_list"),
        "current_subscribe_list",
    )
    current_product_id_list = [
        item.get("product_id") for item in current_subscribe_list if isinstance(item, dict)
    ]
    current_product_ids = set(current_product_id_list)
    show_first_month_price = bool(subscribe_info.get("show_first_month_price"))
    current_member_list = [
        attach_subscribe_info(
            with_member_display_price(product, show_first_month_price),
            current_subscribe_list,
        )
        for product in member_list
        if product.get("product_id") in current_product_ids
    ]
    purchasable_member_list = [
        with_member_display_price(product, show_first_month_price)
        for product in member_list
        if product.get("product_id") not in current_product_ids
        and bool(product.get("available"))
    ]
    hidden_current_subscribed_product_ids = [
        product_id for product_id in current_product_id_list if product_id
    ]
    return {
        "success": True,
        "member_list": [
            with_member_display_price(product, show_first_month_price)
            for product in member_list
        ],
        "purchasable_member_list": purchasable_member_list,
        "current_member_list": current_member_list,
        "current_subscribe_list": current_subscribe_list,
        "hidden_current_subscribed_product_ids": hidden_current_subscribed_product_ids,
        "show_first_month_price": show_first_month_price,
        "show_first_month_price_reason": resolve_first_month_price_reason(subscribe_info),
        "subscribe_info": subscribe_info,
    }


def with_member_display_price(product: Any, show_first_month_price: bool) -> dict[str, Any]:
    item = require_object(product, "member")
    first_month_price_cent = item.get("first_month_price_cent")
    first_month_price_yuan = item.get("first_month_price_yuan")
    renewal_price_yuan = item.get("origin_price_yuan") or item.get("price_yuan")
    can_show_first_month = (
        show_first_month_price
        and isinstance(first_month_price_cent, int)
        and first_month_price_cent > 0
        and isinstance(first_month_price_yuan, str)
        and bool(first_month_price_yuan)
    )
    return {
        **item,
        "show_first_month_price": can_show_first_month,
        "display_price_kind": "first_month" if can_show_first_month else "regular",
        "display_price_yuan": first_month_price_yuan if can_show_first_month else renewal_price_yuan,
        "renewal_price_yuan": renewal_price_yuan,
    }


def attach_subscribe_info(
    product: dict[str, Any],
    subscribe_list: list[Any],
) -> dict[str, Any]:
    product_id = product.get("product_id")
    matched = [
        item for item in subscribe_list
        if isinstance(item, dict) and item.get("product_id") == product_id
    ]
    first_match = matched[0] if matched else {}
    return {
        **product,
        "subscribe_id": first_match.get("subscribe_id"),
        "subscribe_status": first_match.get("subscribe_status"),
        "subscribe_list": matched,
    }


def resolve_first_month_price_reason(subscribe_info: dict[str, Any]) -> str:
    if not subscribe_info.get("hit_first_month_exp"):
        return "miss_first_month_exp"
    if subscribe_info.get("subscribe_list"):
        return "subscribe_list_not_empty"
    if not subscribe_info.get("alipay_first_month_rights"):
        return "no_alipay_first_month_rights"
    return "eligible"


def normalize_create_onetime_response(response: dict[str, Any]) -> dict[str, Any]:
    ensure_success_response(response)
    data = require_object(response.get("data"), "data")
    return with_alipay_payment_skill_hint({**data, "sellerName": SELLER_NAME})


def normalize_create_subscribe_response(response: dict[str, Any]) -> dict[str, Any]:
    ensure_success_response(response)
    data = require_object(response.get("data"), "data")
    alipay_schema = require_text(data.get("alipay_schema"), "data.alipay_schema")
    alipay_schema = build_alipay_subscribe_render_url(alipay_schema)
    alipay_jump_schema = require_text(data.get("alipay_jump_schema"), "data.alipay_jump_schema")
    subscribe_id = require_text(data.get("subscribe_id"), "data.subscribe_id")
    pay_amount = require_int(data.get("pay_amount"), "data.pay_amount")
    qr_filename_prefix = f"alipay-subscribe-{safe_filename(subscribe_id)}-"
    qr_info = create_local_qr_markdown(
        alipay_schema,
        filename=build_subscribe_qr_filename(subscribe_id),
        cleanup_prefix=qr_filename_prefix,
        title="支付宝订阅",
        alt="支付宝订阅二维码",
    )
    return {
        "success": True,
        "code": response.get("code"),
        "msg": response.get("msg"),
        "trace": response.get("trace"),
        "alipay_schema": alipay_schema,
        "alipay_jump_schema": alipay_jump_schema,
        "alipay_schema_qr_path": qr_info["path"],
        "alipay_schema_qr_markdown": qr_info["image_markdown"],
        "alipay_schema_link_markdown": f"[打开支付宝订阅链接]({alipay_schema})",
        "payment_markdown": qr_info["payment_markdown"],
        "subscribe_id": subscribe_id,
        "pay_amount": pay_amount,
        "pay_amount_yuan": format_cent_yuan(pay_amount),
    }


def build_alipay_subscribe_render_url(alipay_schema: str) -> str:
    encoded_schema = urllib.parse.quote(alipay_schema, safe="")
    return (
        "https://render.alipay.com/p/yuyan/180020010001290755/subscribe.html"
        f"?url={encoded_schema}"
    )


def with_alipay_payment_skill_hint(data: dict[str, Any]) -> dict[str, Any]:
    model_data = omit_url_values(data)
    alipay_metadata = data.get("alipayMetadata")
    if isinstance(alipay_metadata, dict):
        model_data["alipayMetadata"] = alipay_metadata
    order_str = resolve_alipay_order_str(data)
    if not order_str:
        return model_data
    return {
        **model_data,
        "payment_skill": ALIPAY_PAYMENT_SKILL_NAME,
        "next_action": f"MUST_CALL_SKILL:{ALIPAY_PAYMENT_SKILL_NAME}",
        "payment_source": 'alipayMetadata["orderStr"]',
        "payment_instruction": (
            "Load the alipay-payment-skill skill and follow that skill's "
            "flow immediately. Use alipayMetadata[\"orderStr\"] as the "
            "cashier_url argument. This value is an Alipay pending-payment "
            "order parameter, not a successful payment result. Do not ask the "
            "user to confirm again, and do not open, rewrite, shorten, "
            "convert, or handle this Alipay value directly."
        ),
    }


def resolve_alipay_order_str(data: dict[str, Any]) -> str | None:
    alipay_metadata = data.get("alipayMetadata")
    if isinstance(alipay_metadata, dict):
        order_str = alipay_metadata.get("orderStr")
        if isinstance(order_str, str) and order_str.strip():
            return order_str.strip()
    return None


def omit_url_values(value: Any) -> Any:
    if isinstance(value, str):
        return OMITTED_FROM_MODEL_OUTPUT if extract_urls(value) else value
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            sanitized_item = omit_url_values(item)
            if sanitized_item is not OMITTED_FROM_MODEL_OUTPUT:
                sanitized[key] = sanitized_item
        return sanitized
    if isinstance(value, list):
        return [
            sanitized_item
            for item in value
            if (sanitized_item := omit_url_values(item)) is not OMITTED_FROM_MODEL_OUTPUT
        ]
    return value


def extract_urls(value: str) -> list[str]:
    return [match.group(0).rstrip("),.;]") for match in URL_RE.finditer(value)]


def normalize_subscribe_info_item(value: Any) -> dict[str, Any]:
    item = require_object(value, "subscribe_info")
    normalized = {
        "subscribe_id": require_text(item.get("subscribe_id"), "subscribe_info.subscribe_id"),
        "subscribe_status": require_text(item.get("subscribe_status"), "subscribe_info.subscribe_status"),
        "product_id": require_text(item.get("product_id"), "subscribe_info.product_id"),
    }
    for field in SUBSCRIBE_VALIDITY_FIELDS:
        value = item.get(field)
        if value is not None and value != "":
            normalized[field] = value
    return normalized


def is_current_subscribe_item(item: dict[str, Any]) -> bool:
    status = str(item.get("subscribe_status", "")).strip().lower()
    return status not in INACTIVE_SUBSCRIBE_STATUSES


def normalize_product(value: Any) -> dict[str, Any]:
    item = require_object(value, "product")
    price_cent = require_int(item.get("product_price"), "product.product_price")
    origin_price_cent = item.get("product_origin_price")
    first_month_price_cent = item.get("product_first_month_price")
    send_score_month = item.get("product_send_score_month")
    send_score_day = item.get("product_send_score_day")
    send_score_forever = item.get("product_send_score_forever")
    send_activity_score = item.get("product_send_activity_score")
    return {
        "product_id": require_text(item.get("product_id"), "product.product_id"),
        "name": require_text(item.get("product_name"), "product.product_name"),
        "description": item.get("product_desc") or "",
        "price_cent": price_cent,
        "price_yuan": f"{price_cent / 100:.2f}",
        "product_type": item.get("product_type"),
        "level": item.get("product_level"),
        "order": item.get("product_order"),
        "period_day": item.get("product_period_day"),
        "origin_price_cent": origin_price_cent,
        "origin_price_yuan": format_cent_yuan(origin_price_cent),
        "first_month_price_cent": first_month_price_cent,
        "first_month_price_yuan": format_cent_yuan(first_month_price_cent),
        "send_score_month": send_score_month,
        "send_score_day": send_score_day,
        "monthly_total_score": (
            send_score_month + send_score_day * 30
            if isinstance(send_score_month, int) and isinstance(send_score_day, int)
            else None
        ),
        "send_score_forever": send_score_forever,
        "send_activity_score": send_activity_score,
        "activity_score_duration": item.get("product_activity_score_duration"),
        "total_score": (
            send_score_forever + send_activity_score
            if isinstance(send_score_forever, int) and isinstance(send_activity_score, int)
            else None
        ),
        "buy_disable": bool(item.get("buy_disable")),
        "available": item.get("status") == 0 and not bool(item.get("buy_disable")),
    }


def format_cent_yuan(value: Any) -> str | None:
    return f"{value / 100:.2f}" if isinstance(value, int) else None


def ensure_success_response(response: dict[str, Any]) -> None:
    if response.get("code") != 0:
        raise AutoClawPayError(f"API returned failure: {response}")
    if not isinstance(response.get("data"), dict):
        raise AutoClawPayError("API response data must be an object")


def parse_json_object(raw: str, label: str) -> dict[str, Any]:
    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError as error:
        raise AutoClawPayError(f"{label} is not valid JSON: {raw[:200]}") from error
    return require_object(parsed, label)


def parse_proxy_stdout_json(raw: str) -> dict[str, Any]:
    raw = raw.lstrip("\ufeff").strip()
    try:
        return parse_json_object(raw, "proxy-trade-request stdout")
    except AutoClawPayError:
        decoder = json.JSONDecoder()
        candidates: list[dict[str, Any]] = []
        for index, char in enumerate(raw):
            if char != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(raw[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                candidates.append(parsed)
        for parsed in reversed(candidates):
            if "code" in parsed and ("data" in parsed or "message" in parsed):
                return parsed
        if candidates:
            return candidates[-1]
        raise AutoClawPayError(f"proxy-trade-request stdout is not valid JSON: {raw[:500]}")


def require_object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AutoClawPayError(f"{name} must be an object")
    return value


def require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise AutoClawPayError(f"{name} must be a list")
    return value


def require_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AutoClawPayError(f"{name} must be a non-empty string")
    return value.strip()


def require_int(value: Any, name: str) -> int:
    if not isinstance(value, int):
        raise AutoClawPayError(f"{name} must be an integer")
    return value


def require_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise AutoClawPayError(f"{name} must be a boolean")
    return value


def extract_token(value: dict[str, Any]) -> str | None:
    for key in ("token", "access_token", "bearer_token"):
        token = extract_string(value, key)
        if token:
            return strip_bearer_prefix(token)
    return None


def extract_string(value: dict[str, Any], key: str) -> str | None:
    raw = value.get(key)
    return raw.strip() if isinstance(raw, str) and raw.strip() else None


def strip_bearer_prefix(value: str) -> str:
    return value.removeprefix("Bearer ").strip()


def join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def resolve_qr_output_dir(preferred_tmp_dir: Path | None = None) -> Path:
    tmp_dir = (
        preferred_tmp_dir
        if preferred_tmp_dir is not None
        else resolve_preferred_openclaw_tmp_dir()
    )
    return tmp_dir / QR_OUTPUT_RELATIVE_DIR


def resolve_preferred_openclaw_tmp_dir() -> Path:
    uid = resolve_effective_uid()
    fallback_name = OPENCLAW_TMP_DIR_NAME if uid is None else f"{OPENCLAW_TMP_DIR_NAME}-{uid}"
    fallback_dir = Path(tempfile.gettempdir()) / fallback_name

    if os.name == "nt":
        return ensure_trusted_tmp_dir(fallback_dir, uid)

    preferred_state = resolve_tmp_dir_state(POSIX_OPENCLAW_TMP_DIR, uid)
    if preferred_state == "available":
        return POSIX_OPENCLAW_TMP_DIR

    if preferred_state == "invalid":
        if try_repair_tmp_dir_writable_bits(POSIX_OPENCLAW_TMP_DIR, uid):
            return POSIX_OPENCLAW_TMP_DIR
        return ensure_trusted_tmp_dir(fallback_dir, uid)

    try:
        if not os.access("/tmp", TMP_DIR_ACCESS_MODE):
            return ensure_trusted_tmp_dir(fallback_dir, uid)

        POSIX_OPENCLAW_TMP_DIR.mkdir(parents=True, mode=0o700, exist_ok=True)
        POSIX_OPENCLAW_TMP_DIR.chmod(0o700)

        if (
            resolve_tmp_dir_state(POSIX_OPENCLAW_TMP_DIR, uid) != "available"
            and not try_repair_tmp_dir_writable_bits(POSIX_OPENCLAW_TMP_DIR, uid)
        ):
            return ensure_trusted_tmp_dir(fallback_dir, uid)

        return POSIX_OPENCLAW_TMP_DIR
    except OSError:
        return ensure_trusted_tmp_dir(fallback_dir, uid)


def resolve_effective_uid() -> int | None:
    if os.name == "nt":
        return None

    getuid = getattr(os, "getuid", None)
    if not callable(getuid):
        return None

    try:
        return int(getuid())
    except OSError:
        return None


def resolve_tmp_dir_state(candidate_path: Path, uid: int | None) -> str:
    try:
        stats = candidate_path.lstat()
        if (
            not stat.S_ISDIR(stats.st_mode)
            or stat.S_ISLNK(stats.st_mode)
            or not is_secure_tmp_dir_for_user(stats, uid)
        ):
            return "invalid"

        if not os.access(candidate_path, TMP_DIR_ACCESS_MODE):
            return "invalid"

        return "available"
    except FileNotFoundError:
        return "missing"
    except OSError:
        return "invalid"


def is_secure_tmp_dir_for_user(stats: os.stat_result, uid: int | None) -> bool:
    if uid is None:
        return True

    if stats.st_uid != uid:
        return False

    return (stats.st_mode & 0o022) == 0


def try_repair_tmp_dir_writable_bits(candidate_path: Path, uid: int | None) -> bool:
    try:
        stats = candidate_path.lstat()
        if not stat.S_ISDIR(stats.st_mode) or stat.S_ISLNK(stats.st_mode):
            return False
        if uid is not None and stats.st_uid != uid:
            return False
        if (stats.st_mode & 0o022) == 0:
            return False

        candidate_path.chmod(0o700)
        return resolve_tmp_dir_state(candidate_path, uid) == "available"
    except OSError:
        return False


def ensure_trusted_tmp_dir(candidate_path: Path, uid: int | None) -> Path:
    state = resolve_tmp_dir_state(candidate_path, uid)
    if state == "available":
        return candidate_path

    if state == "invalid":
        if try_repair_tmp_dir_writable_bits(candidate_path, uid):
            return candidate_path
        raise AutoClawPayError(f"unsafe OpenClaw temp dir: {candidate_path}")

    try:
        candidate_path.mkdir(parents=True, mode=0o700, exist_ok=True)
        candidate_path.chmod(0o700)
    except OSError as error:
        raise AutoClawPayError(f"failed to create OpenClaw temp dir: {candidate_path}") from error

    if (
        resolve_tmp_dir_state(candidate_path, uid) != "available"
        and not try_repair_tmp_dir_writable_bits(candidate_path, uid)
    ):
        raise AutoClawPayError(f"unsafe OpenClaw temp dir: {candidate_path}")

    return candidate_path


def format_display_image_path(path_value: str | Path, platform: str | None = None) -> str:
    media_path = str(path_value)
    current_platform = platform if platform is not None else sys.platform

    if current_platform != "win32":
        return media_path

    if WINDOWS_DRIVE_PATH_RE.match(media_path):
        return format_windows_drive_file_uri(media_path)

    if WINDOWS_UNC_PATH_RE.match(media_path):
        return format_windows_unc_file_uri(media_path)

    if URL_SCHEME_RE.match(media_path):
        return media_path

    return media_path


def format_windows_drive_file_uri(media_path: str) -> str:
    normalized_path = media_path.replace("\\", "/")
    drive = normalized_path[:2]
    rest = normalized_path[2:]
    return f"file:///{drive}{encode_path_segments(rest)}"


def format_windows_unc_file_uri(media_path: str) -> str:
    normalized_path = media_path.replace("\\", "/").lstrip("/")
    return f"file://{encode_path_segments(normalized_path)}"


def encode_path_segments(path_value: str) -> str:
    return "/".join(
        urllib.parse.quote(segment, safe="") for segment in path_value.split("/")
    )


def create_local_qr_markdown(
    value: str,
    filename: str,
    title: str,
    alt: str,
    cleanup_prefix: str | None = None,
) -> dict[str, str]:
    path = create_local_qr_png(value, filename, cleanup_prefix=cleanup_prefix)
    display_path = format_display_image_path(path)
    image_markdown = f"![{alt}]({display_path})"
    payment_markdown = "\n".join(
        [
            f"### {title}",
            image_markdown,
            "",
            f"[打开支付宝订阅链接]({value})",
        ]
    )
    return {
        "path": path,
        "display_path": display_path,
        "image_markdown": image_markdown,
        "payment_markdown": payment_markdown,
    }


def create_local_qr_png(
    value: str,
    filename: str,
    cleanup_prefix: str | None = None,
) -> str:
    try:
        import qrcode  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        ensure_vendor_on_path()
        try:
            import qrcode  # type: ignore[import-not-found]
        except ModuleNotFoundError as error:
            raise AutoClawPayError(
                "missing dependency qrcode. Run: python -m pip install -r scripts/requirements.txt"
            ) from error

    qr_output_dir = resolve_qr_output_dir()
    qr_output_dir.mkdir(parents=True, exist_ok=True)
    cleanup_expired_qr_files(qr_output_dir=qr_output_dir)
    output_path = qr_output_dir / filename
    temp_path = qr_output_dir / f".{filename}.{os.getpid()}.tmp.png"
    image = qrcode.make(value)
    image.save(temp_path)
    temp_path.replace(output_path)
    if cleanup_prefix:
        cleanup_qr_files_with_prefix(qr_output_dir, cleanup_prefix, keep_path=output_path)
    return str(output_path)


def build_subscribe_qr_filename(subscribe_id: str, timestamp: int | None = None) -> str:
    timestamp = timestamp if timestamp is not None else time.time_ns()
    return f"alipay-subscribe-{safe_filename(subscribe_id)}-{timestamp}.png"


def cleanup_qr_files_with_prefix(
    qr_output_dir: Path,
    prefix: str,
    keep_path: Path,
    now: float | None = None,
) -> None:
    current_time = now if now is not None else time.time()
    for path in qr_output_dir.glob(f"{prefix}*.png"):
        try:
            if path == keep_path:
                continue
            if current_time - path.stat().st_mtime < QR_REPLACED_FILE_GRACE_SECONDS:
                continue
            path.unlink()
        except FileNotFoundError:
            continue
        except OSError:
            continue


def cleanup_expired_qr_files(now: float | None = None, qr_output_dir: Path | None = None) -> None:
    output_dir = qr_output_dir if qr_output_dir is not None else resolve_qr_output_dir()
    current_time = now if now is not None else time.time()
    if not should_attempt_qr_cleanup(current_time, output_dir):
        return
    if not try_acquire_cleanup_lock(output_dir):
        return

    started_at = time.monotonic()
    try:
        mark_qr_cleanup_attempt(current_time, output_dir)
        deleted = 0
        for path in output_dir.glob("*.png"):
            if deleted >= QR_CLEANUP_MAX_DELETE:
                break
            if time.monotonic() - started_at > QR_CLEANUP_BUDGET_SECONDS:
                break
            try:
                if current_time - path.stat().st_mtime <= QR_TTL_SECONDS:
                    continue
                path.unlink()
                deleted += 1
            except FileNotFoundError:
                continue
            except OSError:
                continue
    finally:
        release_cleanup_lock(output_dir)


def should_attempt_qr_cleanup(current_time: float, qr_output_dir: Path | None = None) -> bool:
    output_dir = qr_output_dir if qr_output_dir is not None else resolve_qr_output_dir()
    marker_path = output_dir / QR_CLEANUP_MARKER_NAME
    try:
        return current_time - marker_path.stat().st_mtime >= QR_CLEANUP_INTERVAL_SECONDS
    except FileNotFoundError:
        return True
    except OSError:
        return True


def mark_qr_cleanup_attempt(current_time: float, qr_output_dir: Path | None = None) -> None:
    output_dir = qr_output_dir if qr_output_dir is not None else resolve_qr_output_dir()
    marker_path = output_dir / QR_CLEANUP_MARKER_NAME
    try:
        marker_path.touch(exist_ok=True)
        os.utime(marker_path, (current_time, current_time))
    except OSError:
        return


def try_acquire_cleanup_lock(qr_output_dir: Path | None = None) -> bool:
    output_dir = qr_output_dir if qr_output_dir is not None else resolve_qr_output_dir()
    lock_dir = output_dir / QR_CLEANUP_LOCK_NAME
    try:
        lock_dir.mkdir()
        return True
    except FileExistsError:
        clear_stale_cleanup_lock(qr_output_dir)
        try:
            lock_dir.mkdir()
            return True
        except FileExistsError:
            return False
        except OSError:
            return False
    except OSError:
        return False


def clear_stale_cleanup_lock(qr_output_dir: Path | None = None) -> None:
    output_dir = qr_output_dir if qr_output_dir is not None else resolve_qr_output_dir()
    lock_dir = output_dir / QR_CLEANUP_LOCK_NAME
    try:
        age = time.time() - lock_dir.stat().st_mtime
        if age <= QR_CLEANUP_LOCK_STALE_SECONDS:
            return
        lock_dir.rmdir()
    except FileNotFoundError:
        return
    except OSError:
        return


def release_cleanup_lock(qr_output_dir: Path | None = None) -> None:
    output_dir = qr_output_dir if qr_output_dir is not None else resolve_qr_output_dir()
    lock_dir = output_dir / QR_CLEANUP_LOCK_NAME
    try:
        lock_dir.rmdir()
    except FileNotFoundError:
        return
    except OSError:
        return


def ensure_vendor_on_path() -> None:
    vendor = str(VENDOR_DIR)
    if VENDOR_DIR.exists() and vendor not in sys.path:
        sys.path.insert(0, vendor)


def safe_filename(value: str) -> str:
    sanitized = "".join(char if char.isalnum() or char in "._-" else "-" for char in value)
    return sanitized.strip(".-") or hashlib.md5(value.encode("utf-8")).hexdigest()
