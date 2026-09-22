import httpx
import pytest
import respx

from security_core.threat_intel.urlhaus import URL_LOOKUP_ENDPOINT, UrlhausProvider


@pytest.mark.asyncio
@respx.mock
async def test_a_listed_url_is_reported_as_listed() -> None:
    respx.post(URL_LOOKUP_ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "query_status": "ok",
                "threat": "malware_download",
                "tags": ["phishing", "emotet"],
                "urlhaus_reference": "https://urlhaus.abuse.ch/url/12345/",
            },
        )
    )

    result = await UrlhausProvider(auth_key="test-key").check_url("https://evil.example/payload")

    assert result.provider == "urlhaus"
    assert result.status == "listed"
    assert result.threat_type == "malware_download"
    assert result.tags == ["phishing", "emotet"]
    assert result.reference_url == "https://urlhaus.abuse.ch/url/12345/"
    assert result.error is None


@pytest.mark.asyncio
@respx.mock
async def test_an_unlisted_url_is_reported_as_not_listed() -> None:
    respx.post(URL_LOOKUP_ENDPOINT).mock(
        return_value=httpx.Response(200, json={"query_status": "no_results"})
    )

    result = await UrlhausProvider(auth_key="test-key").check_url("https://example.com/")

    assert result.status == "not_listed"
    assert result.error is None


@pytest.mark.asyncio
@respx.mock
async def test_the_auth_key_is_sent_as_a_header_not_a_query_param() -> None:
    route = respx.post(URL_LOOKUP_ENDPOINT).mock(
        return_value=httpx.Response(200, json={"query_status": "no_results"})
    )

    await UrlhausProvider(auth_key="super-secret-key").check_url("https://example.com/")

    assert route.calls.last.request.headers["Auth-Key"] == "super-secret-key"


@pytest.mark.asyncio
@respx.mock
async def test_an_invalid_or_missing_auth_key_degrades_to_unavailable() -> None:
    respx.post(URL_LOOKUP_ENDPOINT).mock(return_value=httpx.Response(401))

    result = await UrlhausProvider(auth_key="wrong-key").check_url("https://example.com/")

    assert result.status == "unavailable"
    assert result.error is not None


@pytest.mark.asyncio
@respx.mock
async def test_timeout_degrades_to_unavailable_rather_than_raising() -> None:
    respx.post(URL_LOOKUP_ENDPOINT).mock(side_effect=httpx.TimeoutException("slow"))

    result = await UrlhausProvider(auth_key="test-key").check_url("https://example.com/")

    assert result.status == "unavailable"
    assert result.error == "timeout"


@pytest.mark.asyncio
@respx.mock
async def test_server_error_degrades_to_unavailable() -> None:
    respx.post(URL_LOOKUP_ENDPOINT).mock(return_value=httpx.Response(500))

    result = await UrlhausProvider(auth_key="test-key").check_url("https://example.com/")

    assert result.status == "unavailable"
    assert result.error is not None


@pytest.mark.asyncio
@respx.mock
async def test_an_unrecognised_query_status_degrades_to_unavailable_not_a_verdict() -> None:
    respx.post(URL_LOOKUP_ENDPOINT).mock(
        return_value=httpx.Response(200, json={"query_status": "invalid_url"})
    )

    result = await UrlhausProvider(auth_key="test-key").check_url("not a url")

    assert result.status == "unavailable"
