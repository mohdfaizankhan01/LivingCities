"""LivingCities scoring engine -- compute the LCUI score from Cognee memory.

For each indicator in ``indicators.yaml`` we ask the ``geneva`` dataset for
evidence and a strict JSON verdict, map verdicts to points, aggregate to pillar
scores and an overall weighted LCUI total, and write ``cache/scorecard.json``
for the API/UI to read.

Because we run against Cognee Cloud (no standalone LLM key), a single
``recall(query_type=RAG_COMPLETION, system_prompt=...)`` call both retrieves the
(French) evidence via vector search and returns the verdict as JSON. A
``CHUNKS`` recall then provides the raw chunk text used to (a) attribute the
evidence to a source filename and (b) verify that the evidence_quote is verbatim.

Run:
    python scoring.py            # use cached verdicts when available
    python scoring.py --no-cache # force fresh recall + LLM verdicts
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional

import cognee
import yaml

from cognee_cloud import CogneeConfigError, connect_cloud, disconnect_cloud

CONFIG_PATH = Path("indicators.yaml")
CACHE_DIR = Path("cache")
SCORES_CACHE = CACHE_DIR / "scores.json"
SCORECARD_PATH = CACHE_DIR / "scorecard.json"
MANIFEST_PATH = CACHE_DIR / "ingest_manifest.json"
DATASET = "geneva_lcui"

VERDICT_POINTS = {"found": 1.0, "partial": 0.5, "not_found": 0.0}

_VERDICT_INTRO = (
    "You are a strict policy evaluator for an ecological urban index. "
    "The source documents are in French; evaluate them regardless of language. "
    "Using ONLY the retrieved context:\n"
    "1. Check the retrieved evidence against each criterion below.\n"
    "2. State in \"reasoning\" (one sentence) which specific criterion IS or IS NOT satisfied.\n"
    "3. Choose the verdict whose criteria are LITERALLY met by the evidence.\n"
    "   - Do NOT judge by feel or inference. "
    "\"found\" wins only when its exact criterion is satisfied.\n"
    "   - If evidence only partially satisfies \"found\", use \"partial\".\n\n"
)
_VERDICT_QUOTE_RULE = (
    "\n\nFor \"evidence_quote\":\n"
    "  - Copy a span VERBATIM from the retrieved text, in its ORIGINAL language "
    "(French stays French -- do NOT translate, paraphrase, or clean up).\n"
    "  - The span must be STRICTLY UNDER 25 words.\n"
    "  - If no suitable verbatim span of under 25 words exists in the retrieved text, "
    "return \"\".\n\n"
    "Respond with ONLY a JSON object, no markdown fences, no prose:\n"
    "{\"verdict\": \"found\" | \"partial\" | \"not_found\", "
    "\"confidence\": <float 0-1>, "
    "\"reasoning\": \"<one sentence stating which criterion is satisfied>\", "
    "\"evidence_quote\": \"<verbatim span from retrieved text, original language, "
    "UNDER 25 words, or empty string>\"}"
)


_TRANSLATE_PROMPT = (
    "You are a French-to-English translator for ecological policy documents. "
    "Your ONLY task is to translate the French text in the user's message to English. "
    "IGNORE any retrieved context -- it is irrelevant to this task. "
    "Return ONLY the English translation as a plain sentence or phrase. "
    "No quotation marks around it, no explanation, no other text."
)


async def translate_quote(text: str) -> str:
    """Translate a short French evidence quote to English via the LLM.

    Uses the same recall_text path as scoring so no extra LLM key is needed.
    Returns an empty string on failure; callers must treat this as optional.
    """
    if not text:
        return ""
    try:
        result = await recall_text(
            f"Translate this French text to English: {text}",
            _TRANSLATE_PROMPT,
        )
        return result.strip()
    except Exception:  # noqa: BLE001 - translation is best-effort
        return ""


def build_verdict_prompt(rubric: dict[str, str] | None) -> str:
    """Build a per-indicator system prompt including rubric criteria when available."""
    if not rubric:
        generic_criteria = (
            "Criteria:\n"
            "  FOUND: clear, specific evidence that directly answers the question.\n"
            "  PARTIAL: some relevant evidence but incomplete or only loosely related.\n"
            "  NOT_FOUND: no relevant evidence in the retrieved context."
        )
        return _VERDICT_INTRO + generic_criteria + _VERDICT_QUOTE_RULE
    criteria = (
        "Criteria:\n"
        f"  FOUND: {rubric.get('found', '')}\n"
        f"  PARTIAL: {rubric.get('partial', '')}\n"
        f"  NOT_FOUND: {rubric.get('not_found', '')}"
    )
    return _VERDICT_INTRO + criteria + _VERDICT_QUOTE_RULE


def load_config(path: Path) -> dict[str, Any]:
    """Load and minimally validate the scoring config."""
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if "pillars" not in config or "score_bands" not in config:
        raise ValueError(f"{path} must define 'pillars' and 'score_bands'")
    return config


def load_json(path: Path, default: Any) -> Any:
    """Read a JSON file, returning ``default`` if it is missing."""
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def band_label(total: int, bands: list[dict[str, Any]]) -> str:
    """Return the score-band label whose [min, max] range contains ``total``."""
    for band in bands:
        if band["min"] <= total <= band["max"]:
            return band["label"]
    return "Unknown"


def strip_fences(text: str) -> str:
    """Remove markdown code fences and language hints around a JSON blob."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned[3:]
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    return cleaned.strip()


def verify_evidence_quote(quote: str, evidence_text: str) -> bool:
    """Return True if ``quote`` (whitespace-normalised, case-insensitive) is a
    substring of ``evidence_text``.  The shared safety guard used by both the
    scoring engine and the /ask endpoint.
    """
    norm_q = " ".join(quote.split()).lower()
    norm_e = " ".join(evidence_text.split()).lower()
    return norm_q in norm_e


def parse_verdict(text: str, evidence_text: str = "") -> Optional[dict[str, Any]]:
    """Parse a verdict JSON string; validate the evidence_quote against retrieved text."""
    try:
        data = json.loads(strip_fences(text))
    except (json.JSONDecodeError, TypeError):
        return None
    if data.get("verdict") not in VERDICT_POINTS:
        return None
    quote = str(data.get("evidence_quote", "") or "")
    truncated = " ".join(quote.split()[:25])

    quote_unverified = False
    if truncated and evidence_text:
        if not verify_evidence_quote(truncated, evidence_text):
            print(f"\n      [UNVERIFIED QUOTE] {truncated[:70]!r}")
            truncated = ""
            quote_unverified = True

    return {
        "verdict": data["verdict"],
        "confidence": round(float(data.get("confidence", 0.0) or 0.0), 2),
        "reasoning": str(data.get("reasoning", "") or "").strip(),
        "evidence_quote": truncated,
        "quote_unverified": quote_unverified,
    }


async def recall_text(question: str, system_prompt: str) -> str:
    """Run a RAG_COMPLETION recall with the given system prompt; return LLM text."""
    results = await cognee.recall(
        question,
        datasets=[DATASET],
        query_type=cognee.SearchType.RAG_COMPLETION,
        system_prompt=system_prompt,
        top_k=10,
    )
    return results[0]["text"] if results else ""


async def _fetch_chunks_raw(question: str) -> list[dict[str, Any]]:
    """Run a CHUNKS recall; return raw chunk list or [] on error."""
    try:
        return await cognee.recall(
            question, datasets=[DATASET],
            query_type=cognee.SearchType.CHUNKS, top_k=10,
        )
    except Exception:  # noqa: BLE001 - provenance is best-effort, never fatal
        return []


async def fetch_chunks(question: str) -> tuple[str, Optional[str]]:
    """Fetch top evidence chunks; return (concatenated_text, top_source_data_id).

    The concatenated text is used to validate that evidence_quote is verbatim.
    The data_id maps to a filename via the ingest manifest.
    """
    chunks = await _fetch_chunks_raw(question)
    if not chunks:
        return "", None
    texts = " ".join(c.get("text", "") or "" for c in chunks if c.get("text"))
    data_id = (chunks[0].get("metadata") or {}).get("data_id")
    return texts, data_id


async def fetch_chunks_for_ask(question: str) -> tuple[str, list[dict[str, Any]]]:
    """Fetch chunks for the /ask endpoint; return (evidence_text, raw_chunks).

    evidence_text drives quote verification; raw_chunks enable per-quote source
    attribution by finding which chunk contains each verified quote.
    """
    chunks = await _fetch_chunks_raw(question)
    if not chunks:
        return "", []
    texts = " ".join(c.get("text", "") or "" for c in chunks if c.get("text"))
    return texts, chunks


_NOT_FOUND_FALLBACK: dict[str, Any] = {
    "verdict": "not_found", "confidence": 0.0,
    "reasoning": "", "evidence_quote": "", "quote_unverified": False,
}


async def judge_indicator(
    question: str,
    rubric: dict[str, str] | None = None,
    evidence_text: str = "",
) -> dict[str, Any]:
    """Retrieve evidence and produce a verdict; retry once on parse failure."""
    prompt = build_verdict_prompt(rubric)
    for attempt in (1, 2):
        try:
            verdict = parse_verdict(await recall_text(question, prompt), evidence_text)
        except Exception as exc:  # noqa: BLE001 - report as an errored verdict
            if attempt == 2:
                return {**_NOT_FOUND_FALLBACK, "error": f"{type(exc).__name__}: {exc}"}
            continue
        if verdict is not None:
            return verdict
    return {**_NOT_FOUND_FALLBACK, "error": "verdict JSON could not be parsed after retry"}


async def score_indicator(
    indicator: dict[str, Any], manifest: dict[str, str],
    cache: dict[str, Any], use_cache: bool,
) -> dict[str, Any]:
    """Score one indicator, using/updating the on-disk cache."""
    iid = indicator["id"]
    if use_cache and iid in cache:
        return cache[iid]

    print(f"    . {iid} ... ", end="", flush=True)
    evidence_text, source_data_id = await fetch_chunks(indicator["question"])
    verdict = await judge_indicator(
        indicator["question"], indicator.get("rubric"), evidence_text
    )
    verdict["source"] = manifest.get(source_data_id) if source_data_id else None
    record = {"id": iid, "question": indicator["question"], **verdict}
    cache[iid] = record
    print(f"{record['verdict']} (conf {record['confidence']})")
    return record


def summarize_pillar(pillar: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a pillar result. Empty pillars are marked not-yet-scored."""
    if not records:
        return {"id": pillar["id"], "name": pillar["name"], "weight": pillar["weight"],
                "score": None, "scored": False, "indicators": []}
    points = sum(VERDICT_POINTS[r["verdict"]] for r in records)
    score = round(points / len(records) * 100)
    return {"id": pillar["id"], "name": pillar["name"], "weight": pillar["weight"],
            "score": score, "scored": True, "indicators": records}


def weighted_total(pillars: list[dict[str, Any]]) -> int:
    """Weighted average of *scored* pillars only (empty pillars are excluded)."""
    scored = [p for p in pillars if p["scored"]]
    total_weight = sum(p["weight"] for p in scored)
    if not total_weight:
        return 0
    return round(sum(p["score"] * p["weight"] for p in scored) / total_weight)


async def build_scorecard(config: dict[str, Any], use_cache: bool) -> dict[str, Any]:
    """Score every indicator and assemble the full scorecard structure."""
    manifest: dict[str, str] = load_json(MANIFEST_PATH, {})
    cache: dict[str, Any] = load_json(SCORES_CACHE, {}) if use_cache else {}

    pillar_results: list[dict[str, Any]] = []
    for pillar in config["pillars"]:
        print(f"  [{pillar['id']}]")
        records = [
            await score_indicator(ind, manifest, cache, use_cache)
            for ind in pillar["indicators"]
        ]
        pillar_results.append(summarize_pillar(pillar, records))

    CACHE_DIR.mkdir(exist_ok=True)
    SCORES_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False),
                            encoding="utf-8")

    total = weighted_total(pillar_results)
    return {"city": "Geneva", "total": total,
            "label": band_label(total, config["score_bands"]),
            "score_bands": config["score_bands"], "pillars": pillar_results}


def print_scorecard(card: dict[str, Any]) -> None:
    """Print a readable scorecard to the console."""
    print("\n" + "=" * 60)
    print(f"  {card['city']} -- LCUI {card['total']}/100  .  {card['label']}")
    print("=" * 60)
    for pillar in card["pillars"]:
        if not pillar["scored"]:
            print(f"\n  {pillar['name']}: (not yet scored -- no indicators)")
            continue
        print(f"\n  {pillar['name']}: {pillar['score']}/100")
        for ind in pillar["indicators"]:
            unverified_tag = " [QUOTE UNVERIFIED]" if ind.get("quote_unverified") else ""
            print(f"    [{ind['verdict']:<9}] {ind['question']}")
            if ind.get("reasoning"):
                print(f"        reasoning: {ind['reasoning']}")
            if ind.get("evidence_quote"):
                src = ind.get("source") or "geneva corpus"
                print(f"        \"{ind['evidence_quote']}\"  -- {src}{unverified_tag}")
            elif ind.get("quote_unverified"):
                print("        (quote blanked -- not verbatim in retrieved text)")
            if ind.get("error"):
                print(f"        ! {ind['error']}")


def _print_audit(card: dict[str, Any], old_scores: dict[str, Any]) -> None:
    """Print quote-unverified flags and verdict changes vs the previous run."""
    unverified: list[str] = []
    changed: list[str] = []

    for pillar in card["pillars"]:
        for ind in pillar["indicators"]:
            iid = ind["id"]
            if ind.get("quote_unverified"):
                unverified.append(f"  {iid}: quote blanked (not verbatim in chunks)")
            old = old_scores.get(iid)
            if old and old.get("verdict") != ind["verdict"]:
                changed.append(
                    f"  {iid}: {old['verdict']} -> {ind['verdict']}"
                    f"  (was conf {old.get('confidence', '?')}, now {ind['confidence']})"
                )

    print("\n" + "-" * 60)
    print("AUDIT -- unverified quotes")
    print("-" * 60)
    if unverified:
        for line in unverified:
            print(line)
    else:
        print("  (none -- all quotes verified as verbatim substrings)")

    print("\n" + "-" * 60)
    print("AUDIT -- verdict changes vs previous run")
    print("-" * 60)
    if changed:
        for line in changed:
            print(line)
    else:
        print("  (none -- all verdicts match the previous run)")


async def main(args: argparse.Namespace) -> int:
    """Connect, score, write scorecard.json, print the scorecard."""
    try:
        config = load_config(CONFIG_PATH)
    except (OSError, ValueError) as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2

    # Capture previous verdicts for change tracking before cache is cleared.
    old_scores: dict[str, Any] = load_json(SCORES_CACHE, {})

    try:
        await connect_cloud()
    except CogneeConfigError as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2

    try:
        card = await build_scorecard(config, use_cache=not args.no_cache)
    finally:
        await disconnect_cloud()

    CACHE_DIR.mkdir(exist_ok=True)
    SCORECARD_PATH.write_text(json.dumps(card, indent=2, ensure_ascii=False),
                              encoding="utf-8")
    print_scorecard(card)
    print(f"\nWrote {SCORECARD_PATH}")
    _print_audit(card, old_scores)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="LivingCities LCUI scoring")
    parser.add_argument("--no-cache", action="store_true",
                        help="Ignore cached verdicts and force fresh recall + LLM.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(asyncio.run(main(parse_args())))
