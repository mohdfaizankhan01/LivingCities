"""Shared Cognee Cloud helpers for LivingCities.

The top-level ``cognee.remember()`` / ``recall()`` functions run against a
*local* embedded database by default. To route them to our Cognee Cloud
tenant we must first call ``cognee.serve(url, api_key)``, which installs a
global remote client so every subsequent operation proxies to the cloud.

This module centralises that connection step and the (slightly fiddly) job
of pulling a readable answer string out of a ``recall()`` result, so both
``smoke_test.py`` and ``ingest.py`` share one implementation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Sequence

import cognee
from dotenv import load_dotenv

class CogneeConfigError(RuntimeError):
    """Raised when required Cognee Cloud configuration is missing."""

@dataclass(frozen=True)
class RememberSummary:
    """Normalized view of a ``remember()`` result.

    ``remember()`` returns a plain ``dict`` when connected to Cognee Cloud but
    a typed ``RememberResult`` object when running locally. This flattens both
    into one shape so callers don't branch on transport.
    """

    status: str
    elapsed_seconds: float
    items_processed: int
    error: str | None
    item_ids: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """True when the pipeline completed without erroring."""
        return self.status not in ("errored", "error") and self.error is None

def summarize_remember(result: Any) -> RememberSummary:
    """Normalize a cloud dict or local RememberResult into a RememberSummary."""
    def field(name: str, default: Any) -> Any:
        if isinstance(result, dict):
            return result.get(name, default)
        return getattr(result, name, default)

    raw_items = field("items", []) or []
    item_ids = tuple(
        str(item.get("id") if isinstance(item, dict) else getattr(item, "id", ""))
        for item in raw_items
    )
    return RememberSummary(
        status=str(field("status", "unknown")),
        elapsed_seconds=float(field("elapsed_seconds", 0.0) or 0.0),
        items_processed=int(field("items_processed", 0) or 0),
        error=field("error", None),
        item_ids=item_ids,
    )

def load_cloud_config() -> tuple[str, str]:
    """Load the Cognee Cloud service URL and API key from the environment.

    Reads ``.env`` (via python-dotenv) then the process environment. Note the
    SDK expects ``COGNEE_SERVICE_URL`` — *not* ``COGNEE_BASE_URL``.

    Returns:
        A ``(service_url, api_key)`` tuple.

    Raises:
        CogneeConfigError: If either variable is unset or empty.
    """
    load_dotenv()
    service_url = os.environ.get("COGNEE_SERVICE_URL", "").strip()
    api_key = os.environ.get("COGNEE_API_KEY", "").strip()

    missing = [
        name
        for name, value in (
            ("COGNEE_SERVICE_URL", service_url),
            ("COGNEE_API_KEY", api_key),
        )
        if not value
    ]
    if missing:
        raise CogneeConfigError(
            "Missing required Cognee Cloud env var(s): "
            f"{', '.join(missing)}. Set them in .env "
            "(COGNEE_SERVICE_URL, not COGNEE_BASE_URL)."
        )
    return service_url, api_key

async def connect_cloud() -> None:
    """Connect the SDK to our Cognee Cloud tenant.

    After this call, ``cognee.remember()`` / ``recall()`` / ``improve()`` /
    ``forget()`` route to the remote instance instead of running locally.

    Raises:
        CogneeConfigError: If configuration is missing.
    """
    service_url, api_key = load_cloud_config()
    await cognee.serve(url=service_url, api_key=api_key)

async def disconnect_cloud() -> None:
    """Close the Cognee Cloud connection, releasing the HTTP session.

    Safe to call in a ``finally`` block; swallows teardown errors so cleanup
    never masks the original result.
    """
    try:
        from cognee.api.v1.serve import state

        client = state.get_remote_client()
        if client is not None and hasattr(client, "close"):
            await client.close()
        await cognee.disconnect()
    except Exception:  # noqa: BLE001 - teardown must not raise
        pass

def extract_answer(results: Sequence[Any]) -> str:
    """Extract a human-readable answer from a ``recall()`` result list.

    ``recall()`` returns a list of typed response entries whose shape depends
    on the search strategy (QA entries expose ``.answer``, graph-completion
    entries may expose ``.text``/``.content``). This walks each entry and
    returns the first non-empty answer-like field it finds, joining multiple
    entries with blank lines.

    Args:
        results: The list returned by ``cognee.recall()``.

    Returns:
        A readable answer string, or an explicit "(no answer ...)" marker so
        empty results are visible rather than silently blank.
    """
    if not results:
        return "(no answer — recall returned no entries)"

    answers: list[str] = []
    for entry in results:
        text = _answer_field(entry)
        if text:
            answers.append(text.strip())

    if not answers:
        return f"(no answer field found in {len(results)} entr(y/ies))"
    return "\n\n".join(answers)

def _answer_field(entry: Any) -> str:
    """Return the best answer-like field from a single recall entry."""
    for attr in ("answer", "text", "content"):
        value = getattr(entry, attr, None)
        if isinstance(value, str) and value.strip():
            return value
    if isinstance(entry, dict):
        for key in ("answer", "text", "content"):
            value = entry.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return ""
