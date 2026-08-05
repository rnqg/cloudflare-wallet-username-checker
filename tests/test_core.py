import httpx
import pytest

from cloudflare_wallet_checker.core import (
    CheckResult,
    CloudflareWalletClient,
    Status,
    normalize_handle,
    parse_api_response,
    unique_handles,
)


def test_normalize_handle() -> None:
    assert normalize_handle(" @Name ") == "name"
    assert normalize_handle("https://cloudflare.pay/?handle=Hello") == "hello"
    assert normalize_handle("https://wallet-name.cloudflare.pay/") == "wallet-name"


def test_unique_handles_preserves_order() -> None:
    assert unique_handles(["One", "@one", "Two"]) == ["one", "two"]


@pytest.mark.parametrize(
    ("status_code", "payload", "expected"),
    [
        (200, {"available": True, "normalized": "free"}, Status.AVAILABLE),
        (200, {"available": False, "code": "TAG_TAKEN"}, Status.TAKEN),
        (
            400,
            {"available": False, "code": "RESERVED_TAG", "error": "reserved"},
            Status.RESERVED,
        ),
        (400, {"available": False, "code": "INVALID_TAG"}, Status.INVALID),
    ],
)
def test_parse_api_response(status_code: int, payload: dict[str, object], expected: Status) -> None:
    assert parse_api_response("name", status_code, payload).status is expected


@pytest.mark.asyncio
async def test_client_uses_api_result() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["tag"] == "free"
        return httpx.Response(200, json={"available": True, "normalized": "free"})

    client = CloudflareWalletClient()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await client.check("free")
    finally:
        await client._client.aclose()
        client._client = None
    assert result == CheckResult("free", Status.AVAILABLE, "free")


@pytest.mark.asyncio
async def test_invalid_handle_skips_network() -> None:
    async with CloudflareWalletClient() as client:
        result = await client.check("ab")
    assert result.status is Status.INVALID
