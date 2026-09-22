"""LLM integration: provider-agnostic client, versioned prompts, structured output.

The LLM only ever *explains* evidence gathered elsewhere (ML, security analysis, RAG) - it never
decides the risk score or classification. `scoring_service` owns that decision; nothing in this
package can override it, because the structured output schema (`schemas.py`) has no field for it.
"""
