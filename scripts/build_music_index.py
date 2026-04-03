#!/usr/bin/env python3
"""
Build a searchable text index from sheet music PDFs.
Extracts whatever text is available (titles, headers, TOC pages).
"""

import json
import os
import re
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

from pypdf import PdfReader


def clean_text(text):
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_pdf_text(pdf_path):
    """Extract text from a PDF. Returns (path, text) or (path, None)."""
    try:
        reader = PdfReader(str(pdf_path))
        # Only read first 10 pages -- that's where titles/TOC live
        texts = []
        for i, page in enumerate(reader.pages[:10]):
            try:
                raw = page.extract_text() or ""
                cleaned = clean_text(raw)
                if cleaned and len(cleaned) > 10:
                    texts.append(cleaned)
            except Exception:
                pass
        if texts:
            return (str(pdf_path), ' '.join(texts))
        return (str(pdf_path), None)
    except Exception:
        return (str(pdf_path), None)


def main():
    sheet_root = Path("sheet_music")
    if not sheet_root.exists():
        print("sheet_music/ not found")
        sys.exit(1)

    # Find all PDFs
    pdfs = list(sheet_root.rglob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs")

    # Extract text in parallel
    workers = os.cpu_count() or 4
    print(f"Extracting text with {workers} workers...")

    results = {}
    extracted = 0
    empty = 0
    start = time.time()

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(extract_pdf_text, p): p for p in pdfs}
        done = 0
        for future in as_completed(futures):
            path, text = future.result()
            done += 1
            if text:
                results[path] = text
                extracted += 1
            else:
                empty += 1
            if done % 100 == 0:
                elapsed = time.time() - start
                print(f"  [{done}/{len(pdfs)}] {extracted} with text, {empty} empty ({elapsed:.0f}s)")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.0f}s")
    print(f"  With text: {extracted}")
    print(f"  Empty: {empty}")

    # Write index
    out_path = "music_text_index.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False)

    size = os.path.getsize(out_path)
    print(f"  Output: {out_path} ({size/1024/1024:.1f} MB)")


if __name__ == "__main__":
    main()
