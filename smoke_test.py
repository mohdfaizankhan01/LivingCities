"""LivingCities smoke test — verify the Cognee Cloud round trip.

Two checks, in order of risk:

1. Text round trip: ``remember()`` a hardcoded sentence, ``recall()`` a
   question about it, print the answer. Proves the cloud connection works.

2. PDF round trip (the real risk): ``remember()`` one real PDF from
   ``./documents/geneva/`` and ``recall()`` a question against it. If native
   ingestion errors, we do NOT retry silently — we report clearly. A
   ``--use-fallback`` flag switches to extracting text locally with
   pdfplumber and remembering the plain text instead.

Run:
    python smoke_test.py                 # native PDF ingestion
    python smoke_test.py --use-fallback  # pdfplumber text extraction first
    python smoke_test.py --pdf path.pdf  # target a specific PDF
"""

from __future__ import annotations

import argparse
import asyncio
import sys
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
TEXT_DATASET = "smoke_text"
PDF_DATASET = "smoke_pdf"


async def check_text_round_trip() -> bool:
    """Remember a hardcoded sentence and recall a question about it.

    Returns:
        True if a non-empty answer came back, False otherwise.
    """
    sentence = (
        "Geneva scores highly on the LCUI ecological framework because it "
        "protects Lake Geneva's water quality and maintains extensive urban "
        "tree canopy."
    )
    print("[1/2] Text round trip")
    print(f"      remember(): {sentence!r}")
    summary = summarize_remember(await cognee.remember(sentence, dataset_name=TEXT_DATASET))
    print(f"      -> status={summary.status} elapsed={summary.elapsed_seconds:.1f}s")
    if not summary.ok:
        print(f"      FAIL: remember errored: {summary.error or summary.status}")
        return False

    question = "Why does Geneva score highly on the LCUI framework?"
    print(f"      recall():   {question!r}")
    answer = extract_answer(await cognee.recall(question, datasets=[TEXT_DATASET]))
    print(f"      answer: {answer}\n")
    return not answer.startswith("(no answer")


def pick_pdf(explicit: str | None) -> Path | None:
    """Choose the PDF to test: an explicit path, else the first in geneva/.

    Args:
        explicit: A user-supplied path, or None to auto-pick.

    Returns:
        A Path to an existing PDF, or None if none is available.
    """
    if explicit:
        path = Path(explicit)
        return path if path.is_file() else None
    if not GENEVA_DIR.is_dir():
        return None
    pdfs = sorted(GENEVA_DIR.glob("*.pdf"))
    return pdfs[0] if pdfs else None


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract plain text from a PDF using pdfplumber (fallback path).

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        The concatenated text of all pages.

    Raises:
        RuntimeError: If pdfplumber is not installed or yields no text.
    """
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover - environment issue
        raise RuntimeError(
            "pdfplumber is required for --use-fallback. Run: pip install pdfplumber"
        ) from exc

    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    text = "\n\n".join(pages).strip()
    if not text:
        raise RuntimeError(
            f"pdfplumber extracted no text from {pdf_path.name} "
            "(likely a scanned/image-only PDF needing OCR)."
        )
    return text


async def check_pdf_round_trip(pdf_path: Path, use_fallback: bool) -> bool:
    """Ingest one PDF (native or via pdfplumber) and recall a question.

    Errors are reported clearly and never retried silently.

    Args:
        pdf_path: The PDF to ingest.
        use_fallback: If True, extract text with pdfplumber and remember the
            plain text; otherwise hand the PDF path to Cognee directly.

    Returns:
        True if a non-empty answer came back, False otherwise.
    """
    mode = "pdfplumber fallback" if use_fallback else "native PDF ingestion"
    print(f"[2/2] PDF round trip ({mode})")
    print(f"      file: {pdf_path}")

    try:
        if use_fallback:
            text = extract_pdf_text(pdf_path)
            print(f"      extracted {len(text):,} chars of text")
            payload: object = text
        else:
            payload = str(pdf_path)
        summary = summarize_remember(
            await cognee.remember(payload, dataset_name=PDF_DATASET)
        )
    except RuntimeError as exc:
        print(f"      FAIL (fallback extraction): {exc}")
        return False
    except Exception as exc:  # noqa: BLE001 - surface the real error, no silent retry
        print(f"      FAIL: remember() raised {type(exc).__name__}: {exc}")
        if not use_fallback:
            print("      HINT: retry with --use-fallback to extract text locally.")
        return False

    print(f"      -> status={summary.status} elapsed={summary.elapsed_seconds:.1f}s")
    if not summary.ok:
        print(f"      FAIL: remember errored: {summary.error or summary.status}")
        if not use_fallback:
            print("      HINT: retry with --use-fallback to extract text locally.")
        return False

    question = "What is this document about? Summarize in one sentence."
    print(f"      recall(): {question!r}")
    try:
        answer = extract_answer(await cognee.recall(question, datasets=[PDF_DATASET]))
    except Exception as exc:  # noqa: BLE001 - surface recall failures explicitly
        print(f"      FAIL: recall() raised {type(exc).__name__}: {exc}")
        return False
    print(f"      answer: {answer}\n")
    return not answer.startswith("(no answer")


async def main(args: argparse.Namespace) -> int:
    """Run both round trips and return a process exit code."""
    try:
        await connect_cloud()
    except CogneeConfigError as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2
    print("Connected to Cognee Cloud.\n")

    try:
        text_ok = await check_text_round_trip()

        pdf_path = pick_pdf(args.pdf)
        if pdf_path is None:
            where = args.pdf or f"{GENEVA_DIR}/*.pdf"
            print(f"[2/2] SKIPPED — no PDF found at {where}. "
                  "Add a city PDF to documents/geneva/ and re-run.")
            pdf_ok = None
        else:
            pdf_ok = await check_pdf_round_trip(pdf_path, args.use_fallback)
    finally:
        await disconnect_cloud()

    print("=" * 50)
    print(f"  text round trip: {'PASS' if text_ok else 'FAIL'}")
    print(f"  pdf round trip:  "
          f"{'SKIPPED' if pdf_ok is None else ('PASS' if pdf_ok else 'FAIL')}")
    print("=" * 50)
    return 0 if text_ok and pdf_ok is not False else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="LivingCities Cognee smoke test")
    parser.add_argument(
        "--use-fallback",
        action="store_true",
        help="Extract PDF text with pdfplumber before remember() instead of "
        "handing the raw PDF to Cognee.",
    )
    parser.add_argument(
        "--pdf",
        default=None,
        help="Path to a specific PDF to test (default: first in documents/geneva/).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(asyncio.run(main(parse_args())))
