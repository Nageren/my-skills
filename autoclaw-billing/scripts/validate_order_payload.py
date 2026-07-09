#!/usr/bin/env python3
"""Validate normalized AutoClaw order payloads.

This script intentionally validates only local payload shape. Availability,
prices, and order status must come from the live AutoClaw source.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


VALID_KINDS = {"monthly_membership", "credit_pack"}
MAX_CONTEXT_VALUE_LENGTH = 256


def fail(message: str) -> None:
    print(f"INVALID: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_payload() -> Any:
    if len(sys.argv) > 2:
        fail("usage: validate_order_payload.py [payload.json]")
    if len(sys.argv) == 2:
        return json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def require_non_empty_string(payload: dict[str, Any], key: str) -> None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{key} must be a non-empty string")


def require_context_string(payload: dict[str, Any], key: str) -> None:
    require_non_empty_string(payload, key)
    value = payload[key].strip()
    if len(value) > MAX_CONTEXT_VALUE_LENGTH:
        fail(f"{key} must be at most {MAX_CONTEXT_VALUE_LENGTH} characters")
    if not all(char.isalnum() or char in "._:-" for char in value):
        fail(f"{key} contains unsupported characters")


def main() -> None:
    payload = load_payload()
    if not isinstance(payload, dict):
        fail("payload must be a JSON object")

    kind = payload.get("kind")
    if kind not in VALID_KINDS:
        fail(f"kind must be one of {sorted(VALID_KINDS)}")

    require_non_empty_string(payload, "item_id")
    require_non_empty_string(payload, "idempotency_key")

    if kind == "monthly_membership":
        require_context_string(payload, "source_id")

    if kind == "credit_pack":
        require_context_string(payload, "framework")
        require_context_string(payload, "session_id")

    quantity = payload.get("quantity", 1)
    if not isinstance(quantity, int) or quantity < 1:
        fail("quantity must be a positive integer")

    print("VALID")


if __name__ == "__main__":
    main()
