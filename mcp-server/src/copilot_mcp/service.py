"""Pure, directly-testable implementations behind each MCP tool in `server.py` - kept separate
from the `@mcp.tool()`-decorated wrappers so tests can call this logic without spinning up the
MCP protocol machinery.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from functools import lru_cache

from qdrant_client import QdrantClient

from copilot_mcp import config
from copilot_mcp.schemas import (
    DnsLookupOut,
    DnsRecordOut,
    DomainInfoOut,
    IndicatorOut,
    KnowledgeSourceOut,
    ThreatIntelOut,
    UrlAnalysisOut,
)
from copilot_ml.inference.predictor import Predictor
from rag_core.ingest import ingest_directory
from rag_core.retriever import retrieve
from rag_core.vector_store import open_client
from security_core.dns_lookup import lookup_dns
from security_core.indicators import evaluate_indicators
from security_core.rdap_lookup import lookup_rdap
from security_core.scoring import score
from security_core.threat_intel import ThreatIntelResult, UrlhausProvider
from security_core.url_validation import InvalidUrlError, validate_and_normalize


class InvalidInputError(ValueError):
    """Tool input a caller should fix and retry - `server.py` turns this into a `ToolError` so
    the model sees a corrective message instead of a stack trace."""


@lru_cache
def _predictor() -> Predictor:
    return Predictor.load(config.ML_MODEL_DIR)


@lru_cache
def _knowledge_client() -> QdrantClient:
    client = open_client(path=config.QDRANT_PATH)
    ingest_directory(client, config.KNOWLEDGE_BASE_DIR)  # idempotent; near-instant once indexed
    return client


async def analyze_url(url: str) -> UrlAnalysisOut:
    try:
        normalized = validate_and_normalize(url)
    except InvalidUrlError as error:
        raise InvalidInputError(str(error)) from error

    predictor = _predictor()
    prediction = await asyncio.to_thread(predictor.predict, normalized.normalized)
    indicators = evaluate_indicators(normalized.normalized)
    result = score(prediction.probability, indicators)

    return UrlAnalysisOut(
        url=normalized.normalized,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        classification=result.classification,
        ml_probability=prediction.probability,
        ml_model_name=predictor.metadata.model_name,
        indicators=[IndicatorOut(**asdict(i)) for i in indicators],
    )


async def lookup_dns_records(host: str) -> DnsLookupOut:
    result = await lookup_dns(host)
    return DnsLookupOut(
        host=result.host,
        resolved=result.resolved,
        records=[
            DnsRecordOut(record_type=rt, values=rec.values, error=rec.error)
            for rt, rec in result.records.items()
        ],
    )


async def check_domain(registered_domain: str) -> DomainInfoOut:
    result = await lookup_rdap(registered_domain)
    return DomainInfoOut(
        domain=result.domain,
        found=result.found,
        registrar=result.registrar,
        created_at=result.created_at.isoformat() if result.created_at else None,
        age_days=result.age_days,
        status=result.status,
        error=result.error,
    )


def _threat_intel_provider() -> UrlhausProvider | None:
    auth_key = config.urlhaus_auth_key()
    return UrlhausProvider(auth_key=auth_key) if auth_key else None


async def threat_lookup(url: str) -> ThreatIntelOut:
    provider = _threat_intel_provider()
    result: ThreatIntelResult = (
        await provider.check_url(url)
        if provider is not None
        else ThreatIntelResult(provider="urlhaus", status="unavailable", error="not_configured")
    )
    return ThreatIntelOut(**asdict(result))


def _search_security_knowledge_sync(query: str, top_k: int) -> list[KnowledgeSourceOut]:
    result = retrieve(_knowledge_client(), query, top_k=top_k)
    return [
        KnowledgeSourceOut(
            chunk_id=c.chunk_id,
            doc_id=c.metadata.get("doc_id"),
            title=c.metadata.get("title"),
            source_name=c.metadata.get("source_name"),
            source_url=c.metadata.get("source_url"),
            topic=c.metadata.get("topic"),
            score=c.score,
            text=c.text,
        )
        for c in result.chunks
    ]


async def search_security_knowledge(query: str, top_k: int = 5) -> list[KnowledgeSourceOut]:
    return await asyncio.to_thread(_search_security_knowledge_sync, query, top_k)
