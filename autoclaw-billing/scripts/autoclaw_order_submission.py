#!/usr/bin/env python3
"""Order submission extension points for AutoClaw payment APIs."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from typing import Any

from autoclaw_pay_client import (
    AutoClawPayClient,
    AutoClawPayError,
    resolve_alipay_bot_bin,
    run_alipay_bot_command,
)


@dataclass(frozen=True)
class OrderSubmissionRequest:
    order_type: str
    product_id: str
    source_id: str | None = None
    product: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OrderReportResult:
    alipay_bot_available: bool
    reported: bool
    skipped_reason: str | None = None
    command: list[str] | None = None
    returncode: int | None = None
    stdout: str | None = None
    stderr: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "alipay_bot_available": self.alipay_bot_available,
            "reported": self.reported,
            **({"skipped_reason": self.skipped_reason} if self.skipped_reason else {}),
            **({"command": self.command} if self.command else {}),
            **({"returncode": self.returncode} if self.returncode is not None else {}),
            **({"stdout": self.stdout} if self.stdout else {}),
            **({"stderr": self.stderr} if self.stderr else {}),
        }


def is_alipay_bot_available() -> bool:
    """Return whether the local alipay-bot executable can be resolved."""
    return resolve_alipay_bot_bin() is not None


class SubmitOrderEvent(ABC):
    """Template method for order submission with pre/post extension points."""

    def __init__(
        self,
        client: AutoClawPayClient,
        *,
        reporter: "OrderInfoReporter | None" = None,
        enable_product_lookup: bool = True,
    ):
        self.client = client
        self.reporter = reporter
        self.enable_product_lookup = enable_product_lookup

    def is_alipay_bot_available(self) -> bool:
        return self.reporter.is_alipay_bot_available()

    def submit(self, request: OrderSubmissionRequest) -> dict[str, Any]:
        prepared = self.before_submit(request)
        result = self.submit_order(prepared)
        self.post_submit_check(prepared, result)
        return self.after_submit(prepared, result)

    def before_submit(self, request: OrderSubmissionRequest) -> OrderSubmissionRequest:
        self.pre_submit_check(request)
        if not self.enable_product_lookup or request.product:
            return request
        return replace(request, product=self.resolve_product(request.product_id))

    def pre_submit_check(self, request: OrderSubmissionRequest) -> None:
        self.validate_request(request)

    @abstractmethod
    def submit_order(self, request: OrderSubmissionRequest) -> dict[str, Any]:
        """Submit the order and return the normalized API response."""

    def after_submit(self, request: OrderSubmissionRequest, result: dict[str, Any]) -> dict[str, Any]:
        # 上报支付宝端侧安全，此处缺失将无法免密支付
        self.reporter.report_after_submit(request, result)
        return {
            **result,
            "order_type": request.order_type,
            "product": request.product
        }

    def post_submit_check(self, request: OrderSubmissionRequest, result: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def resolve_product(self, product_id: str) -> dict[str, Any]:
        """Return the matching normalized product from product-info."""

    def validate_request(self, request: OrderSubmissionRequest) -> None:
        if not request.product_id.strip():
            raise AutoClawPayError("product_id must be a non-empty string")


class CreateOnetimeOrderEvent(SubmitOrderEvent):
    def submit_order(self, request: OrderSubmissionRequest) -> dict[str, Any]:
        return self.client.create_onetime(
            request.product_id,
            session_id=require_metadata_text(request, "session_id"),
        )

    def resolve_product(self, product_id: str) -> dict[str, Any]:
        return find_product(self.client.product_info().get("boost_list", []), product_id, "boost_list")

    def validate_request(self, request: OrderSubmissionRequest) -> None:
        super().validate_request(request)
        require_metadata_text(request, "framework")
        require_metadata_text(request, "session_id")


class CreateSubscribeOrderEvent(SubmitOrderEvent):
    def validate_request(self, request: OrderSubmissionRequest) -> None:
        super().validate_request(request)
        if not request.source_id or not request.source_id.strip():
            raise AutoClawPayError("source_id/session_id must be a non-empty string")

    def submit_order(self, request: OrderSubmissionRequest) -> dict[str, Any]:
        if not request.source_id:
            raise AutoClawPayError("source_id/session_id must be a non-empty string")
        return self.client.create_subscribe(request.source_id, request.product_id)

    def resolve_product(self, product_id: str) -> dict[str, Any]:
        return find_product(self.client.product_info().get("member_list", []), product_id, "member_list")


class OrderInfoReporter(ABC):
    @abstractmethod
    def is_alipay_bot_available(self) -> bool:
        """Return whether the reporter can reach alipay-bot."""

    @abstractmethod
    def report_after_submit(
        self,
        request: OrderSubmissionRequest,
        result: dict[str, Any],
    ) -> OrderReportResult:
        """Report order information after successful order submission."""


class AlipayBotOrderInfoReporter(OrderInfoReporter):
    """Best-effort reporter backed by `alipay-bot trigger-payment-signal`."""

    def __init__(
        self,
        *,
        timeout: int = 10,
    ):
        self.timeout = timeout

    def is_alipay_bot_available(self) -> bool:
        return resolve_alipay_bot_bin() is not None

    def report_after_submit(
        self,
        request: OrderSubmissionRequest,
        result: dict[str, Any],
    ) -> OrderReportResult:
        # return OrderReportResult(
        #     alipay_bot_available=self.is_alipay_bot_available(),
        #     reported=False,
        #     skipped_reason="trigger-payment-signal disabled",
        #     command=None,
        #     returncode=None,
        #     stdout=None,
        #     stderr=None,
        # )
        alipay_bot_bin = resolve_alipay_bot_bin()
        if not alipay_bot_bin:
            return OrderReportResult(
                alipay_bot_available=False,
                reported=False,
                skipped_reason="alipay-bot not found",
            )

        payment_link = resolve_payment_link(result)
        amount = resolve_amount(request, result)
        if not payment_link:
            return OrderReportResult(
                alipay_bot_available=True,
                reported=False,
                skipped_reason="missing payment link",
            )

        command = [
            alipay_bot_bin,
            "trigger-payment-signal",
            "--payment-link",
            payment_link,
            "--merchant-info",
            build_merchant_info(request, result),
        ]
        if amount:
            command.extend(["--amount", amount])

        try:
            completed = run_alipay_bot_command(
                command,
                timeout=self.timeout,
            )
        except Exception as error:
            return OrderReportResult(
                alipay_bot_available=True,
                reported=False,
                skipped_reason=f"report command failed: {error}",
                command=command,
            )

        return OrderReportResult(
            alipay_bot_available=True,
            reported=completed.returncode == 0,
            skipped_reason=None if completed.returncode == 0 else "alipay-bot report failed",
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout.strip() or None,
            stderr=completed.stderr.strip() or None,
        )


def find_product(products: list[Any], product_id: str, list_name: str) -> dict[str, Any]:
    for product in products:
        if isinstance(product, dict) and product.get("product_id") == product_id:
            return product
    raise AutoClawPayError(f"product_id {product_id!r} not found in {list_name}")


def require_metadata_text(request: OrderSubmissionRequest, key: str) -> str:
    value = request.metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AutoClawPayError(f"{key} must be a non-empty string")
    return value.strip()


def resolve_payment_link(result: dict[str, Any]) -> str | None:
    alipay_metadata = result.get("alipayMetadata")
    if isinstance(alipay_metadata, dict):
        order_str = alipay_metadata.get("orderStr")
        if isinstance(order_str, str) and order_str.strip():
            return order_str.strip()

    for key in ("cashier_url", "payment_url"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None



def resolve_amount(request: OrderSubmissionRequest, result: dict[str, Any]) -> str | None:
    product = request.product or {}
    price_cent = product.get("price_cent")
    if isinstance(price_cent, int):
        return cents_to_yuan(price_cent)
    
    metadata = request.metadata or {}
    metadata_amount = metadata.get("price_cent")
    if isinstance(metadata_amount, int):
        return cents_to_yuan(metadata_amount)
    return None


def cents_to_yuan(value: int) -> str:
    return f"{value / 100:.2f}"


def build_merchant_info(request: OrderSubmissionRequest, result: dict[str, Any]) -> str:
    product = request.product or {}
    payload = {
        "order_type": request.order_type,
        "product_id": request.product_id,
        "product_name": product.get("name"),
        "source_id": request.source_id,
        "framework": request.metadata.get("framework"),
        "session_id": request.metadata.get("session_id"),
        "out_trade_no": result.get("out_trade_no"),
        "transaction_id": result.get("transaction_id"),
        "subscribe_id": result.get("subscribe_id"),
        "trace": result.get("trace"),
    }
    compact = {key: value for key, value in payload.items() if value not in (None, "")}
    return json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
