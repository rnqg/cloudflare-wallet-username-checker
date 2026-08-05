from __future__ import annotations

import asyncio
import random
import re
import urllib.parse
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

import httpx

API_URL = "https://cloudflare.pay/api/check"
HANDLE_RE = re.compile(r"^[A-Za-z0-9-]{3,32}$")
RETRYABLE_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}


class Status(str, Enum):
    AVAILABLE = "available"
    TAKEN = "taken"
    RESERVED = "reserved"
    INVALID = "invalid"
    ERROR = "error"


@dataclass(frozen=True)
class CheckResult:
    username: str
    status: Status
    normalized: str | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, str | None]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


def normalize_handle(value: str) -> str:
    value = value.strip()
    if value.startswith("@"):
        value = value[1:]
    if "://" in value:
        parsed = urllib.parse.urlparse(value)
        query = urllib.parse.parse_qs(parsed.query)
        if query.get("handle"):
            value = query["handle"][0]
        elif parsed.hostname and parsed.hostname.endswith(".cloudflare.pay"):
            value = parsed.hostname.removesuffix(".cloudflare.pay")
    return value.strip().lower()


def unique_handles(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    handles: list[str] = []
    for value in values:
        handle = normalize_handle(value)
        if handle and handle not in seen:
            seen.add(handle)
            handles.append(handle)
    return handles


def parse_api_response(username: str, status_code: int, payload: Any) -> CheckResult:
    if not isinstance(payload, dict):
        return CheckResult(
            username, Status.ERROR, detail=f"invalid API response: HTTP {status_code}"
        )
    available = payload.get("available")
    code = payload.get("code")
    normalized_value = payload.get("normalized")
    normalized = normalized_value if isinstance(normalized_value, str) else None
    error = payload.get("error")
    detail = error if isinstance(error, str) else code if isinstance(code, str) else ""
    if available is True and normalized:
        return CheckResult(username, Status.AVAILABLE, normalized)
    if available is False and code == "TAG_TAKEN":
        return CheckResult(username, Status.TAKEN, normalized or username, detail)
    if available is False and code == "RESERVED_TAG":
        return CheckResult(username, Status.RESERVED, normalized or username, detail)
    if available is False and code == "INVALID_TAG":
        return CheckResult(username, Status.INVALID, normalized, detail)
    return CheckResult(
        username,
        Status.ERROR,
        normalized,
        detail or f"unexpected API response: HTTP {status_code}",
    )


def retry_delay(attempt: int, response: httpx.Response | None = None) -> float:
    if response is not None:
        value = response.headers.get("retry-after")
        if value:
            try:
                retry_after = float(value)
                return float(min(max(retry_after, 0.5), 30.0))
            except ValueError:
                pass
    delay = min(0.5 * (2**attempt), 8.0) + random.uniform(0.0, 0.3)
    return float(delay)


class CloudflareWalletClient:
    def __init__(
        self,
        max_connections: int = 10,
        timeout: float = 15.0,
        retries: int = 3,
    ) -> None:
        self.max_connections = max_connections
        self.timeout = timeout
        self.retries = retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> CloudflareWalletClient:
        limits = httpx.Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_connections,
            keepalive_expiry=30.0,
        )
        timeout = httpx.Timeout(self.timeout, connect=self.timeout, pool=self.timeout)
        self._client = httpx.AsyncClient(
            http2=True,
            limits=limits,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "cloudflare-wallet-checker/1.0",
            },
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def check(self, value: str) -> CheckResult:
        username = normalize_handle(value)
        if not HANDLE_RE.fullmatch(username):
            return CheckResult(
                username or value.strip(),
                Status.INVALID,
                detail="use 3-32 characters: A-Z, a-z, 0-9 or hyphen",
            )
        if self._client is None:
            raise RuntimeError("CloudflareWalletClient must be used as an async context manager")
        last_error = "unknown network error"
        for attempt in range(self.retries + 1):
            response: httpx.Response | None = None
            try:
                response = await self._client.get(API_URL, params={"tag": username})
                if response.status_code not in RETRYABLE_HTTP_CODES:
                    try:
                        payload = response.json()
                    except ValueError:
                        last_error = f"invalid JSON response: HTTP {response.status_code}"
                    else:
                        return parse_api_response(username, response.status_code, payload)
                else:
                    last_error = f"HTTP {response.status_code}"
            except httpx.HTTPError as exc:
                last_error = str(exc)
            if attempt < self.retries:
                await asyncio.sleep(retry_delay(attempt, response))
        return CheckResult(username, Status.ERROR, detail=last_error)

    async def check_many(
        self,
        values: Iterable[str],
        workers: int = 5,
        on_result: Callable[[int, int, CheckResult], Awaitable[None] | None] | None = None,
    ) -> list[CheckResult]:
        handles = unique_handles(values)
        semaphore = asyncio.Semaphore(workers)
        results: list[CheckResult | None] = [None] * len(handles)
        completed = 0
        lock = asyncio.Lock()

        async def run(index: int, handle: str) -> None:
            nonlocal completed
            async with semaphore:
                result = await self.check(handle)
            results[index] = result
            async with lock:
                completed += 1
                current = completed
            if on_result is not None:
                callback_result = on_result(current, len(handles), result)
                if callback_result is not None:
                    await callback_result

        await asyncio.gather(*(run(index, handle) for index, handle in enumerate(handles)))
        return [result for result in results if result is not None]
