from app.services.security_analysis_service import _threat_intel_indicators

from security_core.threat_intel import ThreatIntelResult


def test_a_listed_result_becomes_a_high_severity_indicator() -> None:
    result = ThreatIntelResult(provider="urlhaus", status="listed", threat_type="malware_download")
    indicators = _threat_intel_indicators([result])

    assert len(indicators) == 1
    assert indicators[0].code == "threat_intel_hit"
    assert indicators[0].severity == "high"
    assert "malware_download" in indicators[0].title


def test_a_not_listed_result_adds_no_indicator() -> None:
    result = ThreatIntelResult(provider="urlhaus", status="not_listed")
    assert _threat_intel_indicators([result]) == []


def test_an_unavailable_result_adds_no_indicator() -> None:
    result = ThreatIntelResult(provider="urlhaus", status="unavailable", error="timeout")
    assert _threat_intel_indicators([result]) == []


def test_missing_threat_type_falls_back_to_a_generic_label() -> None:
    result = ThreatIntelResult(provider="urlhaus", status="listed", threat_type=None)
    indicators = _threat_intel_indicators([result])
    assert "malicious activity" in indicators[0].title


def test_tags_are_included_in_the_description_when_present() -> None:
    result = ThreatIntelResult(
        provider="urlhaus", status="listed", threat_type="malware_download", tags=["emotet"]
    )
    indicators = _threat_intel_indicators([result])
    assert "emotet" in indicators[0].description


def test_multiple_provider_results_can_each_add_their_own_indicator() -> None:
    results = [
        ThreatIntelResult(provider="urlhaus", status="listed", threat_type="malware_download"),
        ThreatIntelResult(provider="other", status="listed", threat_type="phishing"),
    ]
    indicators = _threat_intel_indicators(results)
    assert len(indicators) == 2
