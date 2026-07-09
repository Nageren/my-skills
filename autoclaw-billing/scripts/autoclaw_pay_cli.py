#!/usr/bin/env python3
"""Command-line wrapper for AutoClaw payment product APIs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from autoclaw_pay_client import (
    CREATE_ONETIME_TRANSPORTS,
    DEFAULT_APP_ID,
    DEFAULT_APP_KEY,
    DEFAULT_BASE_URL,
    DEFAULT_CREATE_ONETIME_TRANSPORT,
    DEFAULT_TOKEN_URL,
    AutoClawPayClient,
    AutoClawPayError,
    ClientConfig,
    resolve_alipay_bot_bin,
)
from autoclaw_order_submission import (
    AlipayBotOrderInfoReporter,
    CreateOnetimeOrderEvent,
    CreateSubscribeOrderEvent,
    OrderSubmissionRequest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AutoClaw payment product API client.")
    add_common_args(parser)

    subparsers = parser.add_subparsers(dest="command", required=True)

    product_info = subparsers.add_parser("product-info", help="List member plans and credit packs.")
    product_info.set_defaults(handler=run_product_info)

    member_list = subparsers.add_parser(
        "member-list",
        help="List monthly membership plans with current subscription filtering.",
    )
    member_list.set_defaults(handler=run_member_list)

    subscribe_info = subparsers.add_parser("subscribe-info", help="Fetch current subscription info.")
    subscribe_info.set_defaults(handler=run_subscribe_info)

    create_onetime = subparsers.add_parser("create-onetime", help="Create one-time credit-pack order.")
    create_onetime.add_argument("--product-id", required=True)
    create_onetime.add_argument(
        "--create-onetime-transport",
        choices=CREATE_ONETIME_TRANSPORTS,
        default=argparse.SUPPRESS,
        help="Transport used by create-onetime. Defaults to alipay-bot-proxy; use mock for local tool testing.",
    )
    create_onetime.add_argument(
        "--framework",
        help="Current framework name for alipay-bot order reporting, e.g. autoclaw.",
    )
    create_onetime.add_argument(
        "--session-id",
        help="Current framework session id for alipay-bot order reporting.",
    )
    create_onetime.add_argument("--report-timeout", type=int, default=10)
    create_onetime.set_defaults(handler=run_create_onetime)

    create_subscribe = subparsers.add_parser("create-subscribe", help="Create monthly subscription order.")
    create_subscribe.add_argument("--source-id")
    create_subscribe.add_argument(
        "--session-id",
        help="Alias for --source-id when source_id is the current framework session id.",
    )
    create_subscribe.add_argument("--product-id", required=True)
    create_subscribe.add_argument("--report-timeout", type=int, default=10)
    create_subscribe.set_defaults(handler=run_create_subscribe)

    runtime_check = subparsers.add_parser("runtime-check", help="Check local runtime environment.")
    runtime_check.set_defaults(handler=run_runtime_check)

    return parser.parse_args()


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--token")
    parser.add_argument("--token-url", default=DEFAULT_TOKEN_URL)
    parser.add_argument("--cookie")
    parser.add_argument("--app-id", default=DEFAULT_APP_ID)
    parser.add_argument("--app-key", default=DEFAULT_APP_KEY)
    parser.add_argument("--timestamp", type=int)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--create-onetime-transport",
        choices=CREATE_ONETIME_TRANSPORTS,
        default=DEFAULT_CREATE_ONETIME_TRANSPORT,
        help="Transport used by create-onetime. Defaults to alipay-bot-proxy; use mock for local tool testing.",
    )
    parser.add_argument("--raw", action="store_true", help="Print raw API response instead of normalized JSON.")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON.")
    parser.add_argument(
        "--output",
        help="Write the JSON result to this UTF-8 file path instead of stdout.",
    )


def build_client(args: argparse.Namespace) -> AutoClawPayClient:
    if not args.app_key:
        raise AutoClawPayError("missing app key. Pass --app-key.")
    return AutoClawPayClient(
        ClientConfig(
            app_id=args.app_id,
            app_key=args.app_key,
            base_url=args.base_url,
            token_url=args.token_url,
            token=args.token,
            cookie=args.cookie,
            timestamp=args.timestamp,
            timeout=args.timeout,
            create_onetime_transport=args.create_onetime_transport,
        )
    )


def run_product_info(args: argparse.Namespace, client: AutoClawPayClient) -> dict[str, Any]:
    return client.raw_product_info() if args.raw else client.product_info()


def run_member_list(args: argparse.Namespace, client: AutoClawPayClient) -> dict[str, Any]:
    if args.raw:
        return {
            "product_info": client.raw_product_info(),
            "subscribe_info": client.raw_subscribe_info(),
        }
    return client.member_list()


def run_subscribe_info(args: argparse.Namespace, client: AutoClawPayClient) -> dict[str, Any]:
    return client.raw_subscribe_info() if args.raw else client.subscribe_info()


def run_create_onetime(args: argparse.Namespace, client: AutoClawPayClient) -> dict[str, Any]:
    if not args.framework or not args.framework.strip():
        raise AutoClawPayError("missing framework. Pass --framework.")
    if not args.session_id or not args.session_id.strip():
        raise AutoClawPayError("missing session id. Pass --session-id.")
    if args.raw:
        return client.raw_create_onetime(args.product_id, session_id=args.session_id.strip())
    event = CreateOnetimeOrderEvent(
        client,
        reporter=build_reporter(args),
    )
    return event.submit(
        OrderSubmissionRequest(
            order_type="credit_pack",
            product_id=args.product_id,
            metadata={
                "framework": args.framework.strip(),
                "session_id": args.session_id.strip(),
            },
        )
    )


def run_create_subscribe(args: argparse.Namespace, client: AutoClawPayClient) -> dict[str, Any]:
    source_id = args.source_id or args.session_id
    if not source_id:
        raise AutoClawPayError("missing source id. Pass --source-id or --session-id.")
    if args.raw:
        return client.raw_create_subscribe(source_id, args.product_id)
    event = CreateSubscribeOrderEvent(
        client,
        reporter=build_reporter(args),
    )
    return event.submit(
        OrderSubmissionRequest(
            order_type="monthly_membership",
            product_id=args.product_id,
            source_id=source_id,
        )
    )


def run_runtime_check(args: argparse.Namespace, _client: AutoClawPayClient | None) -> dict[str, Any]:
    qrcode_available = importlib.util.find_spec("qrcode") is not None
    pillow_available = importlib.util.find_spec("PIL") is not None
    alipay_bot_bin = resolve_alipay_bot_bin()
    alipay_bot_available = alipay_bot_bin is not None
    return {
        "success": True,
        "check": "runtime_environment",
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "qrcode_available": qrcode_available,
        "pillow_available": pillow_available,
        "alipay_bot_bin": alipay_bot_bin,
        "alipay_bot_available": alipay_bot_available,
        "available": qrcode_available and pillow_available and alipay_bot_available,
    }


def build_reporter(args: argparse.Namespace):
    return AlipayBotOrderInfoReporter(
        timeout=args.report_timeout,
    )


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def serialize_json(payload: dict[str, Any], compact: bool) -> str:
    if compact:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(payload, ensure_ascii=False, indent=2)


def emit_json(payload: dict[str, Any], args: argparse.Namespace) -> None:
    output = serialize_json(payload, args.compact)
    if args.output:
        output_path = Path(args.output)
        try:
            if output_path.parent != Path("."):
                output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(f"{output}\n", encoding="utf-8")
        except OSError as error:
            raise AutoClawPayError(f"failed to write output file: {error}") from error
        print_json(
            {
                "success": True,
                "output_path": str(output_path.resolve()),
            },
            compact=True,
        )
        return
    print(output)


def print_json(payload: dict[str, Any], compact: bool) -> None:
    print(serialize_json(payload, compact))


def main() -> int:
    configure_stdio()
    args = parse_args()
    try:
        if args.command == "runtime-check":
            result = args.handler(args, None)
            emit_json(result, args)
            return 0
        client = build_client(args)
        result = args.handler(args, client)
        emit_json(result, args)
        return 0
    except AutoClawPayError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
