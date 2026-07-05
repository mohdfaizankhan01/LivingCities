"""LivingCities ingestion — load source documents into Cognee Cloud memory.

Loads every file in ``documents/geneva/`` into the ``geneva`` dataset and the
dissertation in ``documents/methodology/`` into the ``methodology`` dataset,
streaming per-file progress because cloud ingestion is slow.

IMPORTANT — Cognee Cloud requires file *bytes*, not a path. Passing
``remember(str(path))`` to the cloud stores the literal path string as text
(the server cannot read your local filesystem). We therefore upload an open
binary handle so the server parses the PDF/DOCX itself.

Provenance: to attribute retrieved evidence back to a source filename, we build
a ``data_id -> filename`` manifest. ``remember()`` returns the full item list of
the dataset, so we set-diff the item ids before/after each upload to learn which
id belongs to the file just uploaded, and persist the map to
``cache/ingest_manifest.json`` for scoring.py.

Run:
    python ingest.py                 # ingest geneva + methodology, then sanity queries
    python ingest.py --skip-sanity   # ingest only
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import cognee

from cognee_cloud import (
    CogneeConfigError,
    connect_cloud,
    disconnect_cloud,
    extract_answer,
    summarize_remember,
)

GENEVA_DIR = Path("documents/geneva")
METHODOLOGY_DIR = Path("documents/methodology")
GENEVA_DATASET = "geneva_lcui"
METHODOLOGY_DATASET = "methodology_lcui"

CACHE_DIR = Path("cache")
MANIFEST_PATH = CACHE_DIR / "ingest_manifest.json"

SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md", ".docx"}

SANITY_QUERIES = [
    "What measures does Geneva propose to protect biodiversity?",
    "Are there policies about ecological corridors or biological connectivity?",
    "What does the plan say about urban trees or green infrastructure?",
]

def list_documents(directory: Path) -> list[Path]:
    """Return supported source files in a directory, sorted by name."""
    if not directory.is_dir():
        return []
    return sorted(
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )

async def ingest_file(
    path: Path, dataset: str, seen_ids: set[str]
) -> tuple[bool, dict[str, str]]:
    """Upload one file's bytes into a dataset and map new item ids to its name.

    Args:
        path: File to ingest.
        dataset: Target Cognee dataset name.
        seen_ids: Item ids already present before this upload; updated in place.

    Returns:
        ``(ok, mapping)`` where mapping is ``{data_id: filename}`` for the items
        this upload introduced. ``ok`` is False if ``remember()`` failed.
    """
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"  → {path.name} ({size_mb:.1f} MB) ... ", end="", flush=True)
    start = time.perf_counter()
    try:
        with path.open("rb") as handle:
            summary = summarize_remember(
                await cognee.remember(handle, dataset_name=dataset)
            )
    except Exception as exc:  # noqa: BLE001 - surface real failure, never silent
        print(f"FAIL after {time.perf_counter() - start:.1f}s — "
              f"{type(exc).__name__}: {exc}")
        return False, {}

    elapsed = time.perf_counter() - start
    if not summary.ok:
        print(f"FAIL after {elapsed:.1f}s — status={summary.status} "
              f"error={summary.error}")
        return False, {}

    new_ids = [item_id for item_id in summary.item_ids if item_id not in seen_ids]
    seen_ids.update(summary.item_ids)
    mapping = {item_id: path.name for item_id in new_ids}
    print(f"OK  status={summary.status} new_items={len(new_ids)} ({elapsed:.1f}s)")
    return True, mapping

async def ingest_directory(
    directory: Path, dataset: str
) -> tuple[int, int, dict[str, str]]:
    """Ingest every supported file in a directory into a dataset.

    Returns:
        ``(succeeded, total, manifest)`` where manifest is ``{data_id: filename}``.
    """
    files = list_documents(directory)
    print(f"\n[{dataset}] {len(files)} file(s) from {directory}/")
    if not files:
        print(f"  (no supported files found in {directory}/)")
        return 0, 0, {}

    succeeded = 0
    seen_ids: set[str] = set()
    manifest: dict[str, str] = {}
    for index, path in enumerate(files, start=1):
        print(f"[{dataset}] {index}/{len(files)}", end="")
        ok, mapping = await ingest_file(path, dataset, seen_ids)
        succeeded += int(ok)
        manifest.update(mapping)
    print(f"[{dataset}] done: {succeeded}/{len(files)} succeeded")
    return succeeded, len(files), manifest

def save_manifest(manifest: dict[str, str]) -> None:
    """Persist the ``data_id -> filename`` map for scoring.py provenance."""
    CACHE_DIR.mkdir(exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nWrote provenance manifest ({len(manifest)} items) to {MANIFEST_PATH}")

async def run_sanity_queries(dataset: str) -> None:
    """Run a few recall() queries and print answers to eyeball quality."""
    print(f"\n=== sanity recall() against '{dataset}' ===")
    for query in SANITY_QUERIES:
        print(f"\nQ: {query}")
        try:
            answer = extract_answer(await cognee.recall(query, datasets=[dataset]))
        except Exception as exc:  # noqa: BLE001 - report, don't crash the run
            print(f"A: (recall failed — {type(exc).__name__}: {exc})")
            continue
        print(f"A: {answer}")

async def main(args: argparse.Namespace) -> int:
    """Connect, (optionally) reset, ingest both datasets, sanity-check."""
    try:
        await connect_cloud()
    except CogneeConfigError as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2
    print("Connected to Cognee Cloud.")

    try:
        geneva_ok, geneva_total, manifest = await ingest_directory(
            GENEVA_DIR, GENEVA_DATASET
        )
        _, _, method_manifest = await ingest_directory(
            METHODOLOGY_DIR, METHODOLOGY_DATASET
        )
        manifest.update(method_manifest)
        save_manifest(manifest)

        if geneva_ok == 0:
            print("\nERROR: no Geneva documents ingested — cannot score. Aborting.")
            return 1

        if not args.skip_sanity:
            await run_sanity_queries(GENEVA_DATASET)
    finally:
        await disconnect_cloud()

    print(f"\nIngestion complete. Geneva: {geneva_ok}/{geneva_total} documents.")
    return 0

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="LivingCities document ingestion")
    parser.add_argument("--skip-sanity", action="store_true",
                        help="Skip the post-ingestion sanity recall() queries.")
    return parser.parse_args(argv)

if __name__ == "__main__":
    sys.exit(asyncio.run(main(parse_args())))
