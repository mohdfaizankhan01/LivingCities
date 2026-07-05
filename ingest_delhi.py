"""Ingest Delhi documents into the delhi_lcui Cognee dataset.

Thin wrapper around the generic ingest helpers in ingest.py.  Writes a
Delhi-specific manifest to cache/ingest_manifest_delhi.json.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import cognee

from cognee_cloud import CogneeConfigError, connect_cloud, disconnect_cloud, extract_answer
from ingest import ingest_directory

DELHI_DIR = Path("documents/delhi")
DELHI_DATASET = "delhi_lcui"
MANIFEST_DELHI = Path("cache/ingest_manifest_delhi.json")

SANITY_QUERIES = [
    "What does DDA say about biodiversity parks and native species in Delhi?",
    "What is the tree cover percentage or green area target in Delhi?",
    "What governance structure does Delhi have for climate adaptation?",
]


async def main() -> int:
    try:
        await connect_cloud()
    except CogneeConfigError as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2
    print("Connected to Cognee Cloud.")

    try:
        ok, total, manifest = await ingest_directory(DELHI_DIR, DELHI_DATASET)

        Path("cache").mkdir(exist_ok=True)
        MANIFEST_DELHI.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"\nWrote Delhi manifest ({len(manifest)} items) to {MANIFEST_DELHI}")

        if ok == 0:
            print("ERROR: no Delhi documents ingested.")
            return 1

        print(f"\n=== sanity recall() against '{DELHI_DATASET}' ===")
        for query in SANITY_QUERIES:
            print(f"\nQ: {query}")
            try:
                answer = extract_answer(await cognee.recall(query, datasets=[DELHI_DATASET]))
                print(f"A: {answer}")
            except Exception as exc:  # noqa: BLE001
                print(f"A: (failed — {type(exc).__name__}: {exc})")
    finally:
        await disconnect_cloud()

    print(f"\nIngestion complete: {ok}/{total} documents.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
