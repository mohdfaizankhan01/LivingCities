"""Score Delhi against the same 20 LCUI indicators used for Geneva.

Monkey-patches scoring.DATASET / SCORECARD_PATH / MANIFEST_PATH to point at
delhi_lcui before calling build_scorecard -- no logic changes to scoring.py.
Output: cache/scorecard_delhi.json
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import scoring
from cognee_cloud import CogneeConfigError, connect_cloud, disconnect_cloud

scoring.DATASET = "delhi_lcui"
scoring.SCORECARD_PATH = Path("cache/scorecard_delhi.json")
scoring.MANIFEST_PATH = Path("cache/ingest_manifest_delhi.json")
scoring.SCORES_CACHE = Path("cache/scores_delhi.json")

async def main() -> int:
    try:
        config = scoring.load_config(scoring.CONFIG_PATH)
    except (OSError, ValueError) as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2

    try:
        await connect_cloud()
    except CogneeConfigError as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2

    try:
        card = await scoring.build_scorecard(config, use_cache=False)
    finally:
        await disconnect_cloud()

    card["city"] = "Delhi"
    Path("cache").mkdir(exist_ok=True)
    scoring.SCORECARD_PATH.write_text(
        json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    scoring.print_scorecard(card)
    print(f"\nWrote {scoring.SCORECARD_PATH}")

    unverified = [
        ind["id"]
        for pillar in card["pillars"]
        for ind in pillar["indicators"]
        if ind.get("quote_unverified")
    ]
    print("\n--- AUDIT: unverified quotes ---")
    if unverified:
        for iid in unverified:
            print(f"  {iid}")
    else:
        print("  (none)")

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
