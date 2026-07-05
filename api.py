"""LivingCities backend API — serves the LCUI scorecard and memory demos.

Thin FastAPI layer over ``scoring.py`` (all scoring logic is imported, not
duplicated). Endpoints:

    GET  /health    -> liveness probe
    GET  /cities    -> list of available cities with scores
    GET  /score     -> current scorecard (builds once if missing); ?city=
    POST /feedback  -> expert correction: remember() + improve(), re-score one
                       indicator, return the updated indicator + new total
    POST /forget    -> remove a document/dataset from memory, re-score, return
                       the new scorecard (a repealed policy drops the score)
    POST /ask       -> free-form Q&A grounded in ingested documents; ?city=

Cognee Cloud is connected once at startup and reused for every request.
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Optional
from uuid import UUID

import cognee
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import scoring
from cognee_cloud import connect_cloud, disconnect_cloud

FEEDBACK_SESSION = "expert_feedback"

# City registry: id -> config.  Adding a new city = adding one entry here.
CITY_CONFIGS: dict[str, dict[str, Any]] = {
    "geneva": {
        "name": "Geneva",
        "scorecard_path": scoring.SCORECARD_PATH,
        "dataset": "geneva_lcui",
        "manifest_path": scoring.MANIFEST_PATH,
    },
    "delhi": {
        "name": "Delhi",
        "scorecard_path": scoring.CACHE_DIR / "scorecard_delhi.json",
        "dataset": "delhi_lcui",
        "manifest_path": scoring.CACHE_DIR / "ingest_manifest_delhi.json",
    },
}

# Grounded Q&A prompt for /ask.
_ASK_SYSTEM_PROMPT = (
    "You are a grounded Q&A assistant for LivingCities. "
    "Answer the user's question using ONLY the retrieved evidence. "
    "Do NOT use outside knowledge.\n"
    "If the retrieved evidence does not contain the answer, set grounded to false "
    "and answer exactly: \"The ingested documents don't cover this.\"\n"
    "Otherwise write a short answer (2-3 sentences max) and include up to 2 "
    "verbatim spans from the retrieved text as quotes.\n"
    "Each quote must be copied VERBATIM from the retrieved text in its ORIGINAL "
    "language (French stays French -- do NOT translate, paraphrase, or clean up).\n"
    "Each quote must be STRICTLY UNDER 25 words.\n"
    "If no verbatim span under 25 words exists in the retrieved text, leave quotes empty.\n\n"
    "Respond with ONLY this JSON, no markdown fences, no prose:\n"
    "{\"answer\": \"<2-3 sentence answer or not-covered message>\", "
    "\"grounded\": <true|false>, "
    "\"quotes\": [{\"text\": \"<verbatim span, original language, under 25 words>\"}]}"
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Connect to Cognee Cloud for the app's lifetime."""
    await connect_cloud()
    try:
        yield
    finally:
        await disconnect_cloud()


app = FastAPI(title="LivingCities API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class FeedbackBody(BaseModel):
    indicator_id: str
    correction_text: str


class ForgetBody(BaseModel):
    target: str


class AskBody(BaseModel):
    question: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_ask_response(text: str) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(scoring.strip_fences(text))
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data.get("answer"), str):
        return None
    return data


def _find_quote_source(
    quote: str, chunks: list[dict[str, Any]], manifest: dict[str, str]
) -> str:
    norm_q = " ".join(quote.split()).lower()
    for chunk in chunks:
        chunk_text = " ".join((chunk.get("text", "") or "").split()).lower()
        if norm_q in chunk_text:
            data_id = (chunk.get("metadata") or {}).get("data_id")
            if data_id and data_id in manifest:
                return manifest[data_id]
    return "corpus"


def error(message: str, status: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


def find_indicator(config: dict[str, Any], indicator_id: str) -> Optional[tuple[dict, dict]]:
    for pillar in config["pillars"]:
        for indicator in pillar["indicators"]:
            if indicator["id"] == indicator_id:
                return pillar, indicator
    return None


def recompute(card: dict[str, Any], config: dict[str, Any]) -> None:
    for pillar in card["pillars"]:
        records = pillar["indicators"]
        if records:
            points = sum(scoring.VERDICT_POINTS[r["verdict"]] for r in records)
            pillar["score"] = round(points / len(records) * 100)
            pillar["scored"] = True
    card["total"] = scoring.weighted_total(card["pillars"])
    card["label"] = scoring.band_label(card["total"], config["score_bands"])


async def _add_translations(card: dict[str, Any]) -> dict[str, Any]:
    """Translate every evidence_quote that lacks evidence_quote_en (in parallel)."""
    needs = [
        ind
        for pillar in card.get("pillars", [])
        for ind in pillar.get("indicators", [])
        if ind.get("evidence_quote") and not ind.get("evidence_quote_en")
    ]
    if not needs:
        return card
    print(f"  Translating {len(needs)} evidence quote(s)...")
    results = await asyncio.gather(
        *[scoring.translate_quote(ind["evidence_quote"]) for ind in needs],
        return_exceptions=True,
    )
    for ind, result in zip(needs, results):
        ind["evidence_quote_en"] = result if isinstance(result, str) else ""
    return card


def _save_scorecard(card: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")


async def ensure_scorecard_for(city: str) -> dict[str, Any]:
    """Load (or build) a city scorecard, add English translations, and cache."""
    cfg = CITY_CONFIGS[city]
    existing = scoring.load_json(cfg["scorecard_path"], None)
    if existing is not None:
        card = existing
    else:
        if city != "geneva":
            raise FileNotFoundError(
                f"No cached scorecard for '{city}'. Run score_{city}.py first."
            )
        config = scoring.load_config(scoring.CONFIG_PATH)
        card = await scoring.build_scorecard(config, use_cache=True)

    card = await _add_translations(card)
    _save_scorecard(card, cfg["scorecard_path"])
    return card


# Legacy alias for Geneva-only endpoints.
async def ensure_scorecard() -> dict[str, Any]:
    return await ensure_scorecard_for("geneva")


def save_card(card: dict[str, Any]) -> None:
    _save_scorecard(card, scoring.SCORECARD_PATH)


# City-parameterised recall helpers (avoid monkey-patching scoring.DATASET).
async def _fetch_chunks_city(
    question: str, dataset: str
) -> tuple[str, list[dict[str, Any]]]:
    try:
        chunks = await cognee.recall(
            question, datasets=[dataset],
            query_type=cognee.SearchType.CHUNKS, top_k=10,
        )
    except Exception:  # noqa: BLE001
        return "", []
    if not chunks:
        return "", []
    texts = " ".join(c.get("text", "") or "" for c in chunks if c.get("text"))
    return texts, list(chunks)


async def _recall_city(question: str, system_prompt: str, dataset: str) -> str:
    results = await cognee.recall(
        question,
        datasets=[dataset],
        query_type=cognee.SearchType.RAG_COMPLETION,
        system_prompt=system_prompt,
        top_k=10,
    )
    return results[0]["text"] if results else ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/cities")
async def get_cities() -> Any:
    """List all cities that have a cached scorecard."""
    result = []
    for city_id, cfg in CITY_CONFIGS.items():
        card = scoring.load_json(cfg["scorecard_path"], None)
        if card is not None:
            result.append({
                "id": city_id,
                "name": cfg["name"],
                "total": card.get("total", 0),
                "label": card.get("label", "Unknown"),
            })
    return {"cities": result}


@app.get("/documents")
async def get_documents(city: str = "geneva") -> dict[str, list[str]]:
    cfg = CITY_CONFIGS.get(city, CITY_CONFIGS["geneva"])
    manifest: dict[str, str] = scoring.load_json(cfg["manifest_path"], {})
    return {"documents": sorted(set(manifest.values()))}


@app.get("/score")
async def get_score(city: str = "geneva") -> Any:
    """Return the current scorecard for a city (default: geneva)."""
    if city not in CITY_CONFIGS:
        return error(f"Unknown city: {city}", status=404)
    try:
        return await ensure_scorecard_for(city)
    except Exception as exc:  # noqa: BLE001
        return error(f"Could not produce scorecard: {exc}", status=500)


@app.post("/feedback")
async def post_feedback(body: FeedbackBody) -> Any:
    """Ingest an expert correction and re-score the affected indicator (Geneva only)."""
    if not body.correction_text.strip():
        return error("correction_text must not be empty")
    try:
        config = scoring.load_config(scoring.CONFIG_PATH)
    except Exception as exc:  # noqa: BLE001
        return error(f"Config error: {exc}", status=500)

    match = find_indicator(config, body.indicator_id)
    if match is None:
        return error(f"Unknown indicator_id: {body.indicator_id}", status=404)
    _, indicator = match

    try:
        await cognee.remember(body.correction_text, dataset_name=scoring.DATASET,
                              session_id=FEEDBACK_SESSION)
        await cognee.remember(body.correction_text, dataset_name=scoring.DATASET)
    except Exception as exc:  # noqa: BLE001
        return error(f"Feedback ingestion failed: {exc}", status=502)

    try:
        await cognee.improve(dataset=scoring.DATASET)
    except Exception as exc:  # noqa: BLE001
        print(f"improve() skipped: {exc}")

    try:
        manifest = scoring.load_json(scoring.MANIFEST_PATH, {})
        record = await scoring.score_indicator(indicator, manifest, {}, use_cache=False)
    except Exception as exc:  # noqa: BLE001
        return error(f"Re-scoring failed: {exc}", status=502)

    card = await ensure_scorecard()
    for pillar in card["pillars"]:
        pillar["indicators"] = [
            record if r["id"] == record["id"] else r for r in pillar["indicators"]
        ]
    recompute(card, config)
    save_card(card)
    return {"indicator": record, "total": card["total"], "label": card["label"]}


@app.post("/ask")
async def post_ask(body: AskBody, city: str = "geneva") -> Any:
    """Answer a free-form question grounded in the ingested documents for a city."""
    if city not in CITY_CONFIGS:
        return error(f"Unknown city: {city}", status=404)

    cfg = CITY_CONFIGS[city]
    dataset = cfg["dataset"]
    question = body.question.strip()
    if not question:
        return error("question must not be empty")

    try:
        evidence_text, raw_chunks = await _fetch_chunks_city(question, dataset)
    except Exception as exc:  # noqa: BLE001
        return error(f"Evidence retrieval failed: {exc}", status=502)

    parsed = None
    for attempt in (1, 2):
        try:
            raw = await _recall_city(question, _ASK_SYSTEM_PROMPT, dataset)
            parsed = _parse_ask_response(raw)
            if parsed is not None:
                break
        except Exception as exc:  # noqa: BLE001
            if attempt == 2:
                return error(f"Ask failed: {exc}", status=502)

    if parsed is None:
        return error("Could not parse grounded answer after retry", status=502)

    manifest: dict[str, str] = scoring.load_json(cfg["manifest_path"], {})

    verified_quotes: list[dict[str, str]] = []
    for q in parsed.get("quotes", []) or []:
        text = " ".join(str(q.get("text", "") or "").split()[:25])
        if not text:
            continue
        if not scoring.verify_evidence_quote(text, evidence_text):
            print(f"[ask/{city}] UNVERIFIED QUOTE dropped: {text[:70]!r}")
            continue
        verified_quotes.append({
            "text": text,
            "source": _find_quote_source(text, raw_chunks, manifest),
        })

    grounded = bool(parsed.get("grounded", False))
    answer = str(parsed.get("answer", "") or "").strip()

    if grounded and not verified_quotes and evidence_text:
        grounded = False
        answer = "The ingested documents don't cover this."

    if verified_quotes:
        translations = await asyncio.gather(
            *[scoring.translate_quote(q["text"]) for q in verified_quotes],
            return_exceptions=True,
        )
        for q, t in zip(verified_quotes, translations):
            q["translation"] = t if isinstance(t, str) else ""

    return {"answer": answer, "grounded": grounded, "quotes": verified_quotes}


@app.post("/forget")
async def post_forget(body: ForgetBody) -> Any:
    """Remove a document (by filename) or whole dataset, then re-score (Geneva only)."""
    target = body.target.strip()
    if not target:
        return error("target must not be empty")

    manifest: dict[str, str] = scoring.load_json(scoring.MANIFEST_PATH, {})
    data_ids = [did for did, name in manifest.items() if name == target]

    try:
        if data_ids:
            for data_id in data_ids:
                await cognee.forget(data_id=UUID(data_id), dataset=scoring.DATASET)
        elif target in (scoring.DATASET, "all"):
            await cognee.forget(dataset=scoring.DATASET)
        else:
            return error(f"Unknown target '{target}' (not a known document or dataset)",
                         status=404)
    except Exception as exc:  # noqa: BLE001
        return error(f"forget() failed: {exc}", status=502)

    try:
        config = scoring.load_config(scoring.CONFIG_PATH)
        card = await scoring.build_scorecard(config, use_cache=False)
    except Exception as exc:  # noqa: BLE001
        return error(f"Re-scoring after forget failed: {exc}", status=502)
    save_card(card)
    return card
