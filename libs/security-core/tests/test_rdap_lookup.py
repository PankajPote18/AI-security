import httpx
import pytest
import respx

from security_core.rdap_lookup import RDAP_BASE_URL, lookup_rdap

_SAMPLE_RESPONSE = {
    "objectClassName": "domain",
    "handle": "EXAMPLE.COM",
    "status": ["client transfer prohibited"],
    "entities": [
        {
            "roles": ["registrar"],
            "vcardArray": [
                "vcard",
                [["version", {}, "text", "4.0"], ["fn", {}, "text", "Example Registrar, Inc."]],
            ],
        }
    ],
    "events": [
        {"eventAction": "registration", "eventDate": "1995-08-14T04:00:00Z"},
        {"eventAction": "last changed", "eventDate": "2024-08-13T07:01:44Z"},
    ],
}


@pytest.mark.asyncio
@respx.mock
async def test_found_domain_is_parsed() -> None:
    respx.get(f"{RDAP_BASE_URL}/example.com").mock(
        return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
    )

    result = await lookup_rdap("example.com")

    assert result.found
    assert result.registrar == "Example Registrar, Inc."
    assert result.created_at is not None
    assert result.created_at.year == 1995
    assert result.age_days is not None
    assert result.age_days > 10_000  # registered in 1995
    assert "client transfer prohibited" in result.status


@pytest.mark.asyncio
@respx.mock
async def test_redirect_to_the_authoritative_registry_is_followed() -> None:
    # Regression: rdap.org deliberately 302-redirects every lookup to the registry's own RDAP
    # server; without follow_redirects=True this silently produced found=False for every domain.
    respx.get(f"{RDAP_BASE_URL}/example.com").mock(
        return_value=httpx.Response(
            302, headers={"location": "https://rdap.verisign.com/com/v1/domain/example.com"}
        )
    )
    respx.get("https://rdap.verisign.com/com/v1/domain/example.com").mock(
        return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
    )

    result = await lookup_rdap("example.com")

    assert result.found
    assert result.registrar == "Example Registrar, Inc."


@pytest.mark.asyncio
@respx.mock
async def test_not_found_domain_returns_found_false() -> None:
    respx.get(f"{RDAP_BASE_URL}/never-registered-xyz123.example").mock(
        return_value=httpx.Response(404)
    )

    result = await lookup_rdap("never-registered-xyz123.example")

    assert result.found is False
    assert result.error is None
    assert result.age_days is None


@pytest.mark.asyncio
@respx.mock
async def test_timeout_is_reported_gracefully() -> None:
    respx.get(f"{RDAP_BASE_URL}/slow.example").mock(side_effect=httpx.TimeoutException("slow"))

    result = await lookup_rdap("slow.example")

    assert result.found is False
    assert result.error == "timeout"


@pytest.mark.asyncio
@respx.mock
async def test_server_error_is_reported_gracefully() -> None:
    respx.get(f"{RDAP_BASE_URL}/broken.example").mock(return_value=httpx.Response(500))

    result = await lookup_rdap("broken.example")

    assert result.found is False
    assert result.error is not None


@pytest.mark.asyncio
@respx.mock
async def test_missing_events_and_entities_do_not_raise() -> None:
    respx.get(f"{RDAP_BASE_URL}/sparse.example").mock(
        return_value=httpx.Response(200, json={"objectClassName": "domain"})
    )

    result = await lookup_rdap("sparse.example")

    assert result.found
    assert result.registrar is None
    assert result.created_at is None
    assert result.status == []
