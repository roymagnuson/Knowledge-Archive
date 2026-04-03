#!/usr/bin/env python3
"""
Build a searchable JSON index from medical/survival PDFs and EMERGENCY_KNOWLEDGE.txt.
Run from the EmergencyKnowledge directory.
"""

import json
import os
import re
import sys
from pathlib import Path

from pypdf import PdfReader


def clean_text(text: str) -> str:
    """Collapse whitespace and strip control characters."""
    # Remove control chars except newline/tab
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # Collapse whitespace runs into single spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def title_from_filename(filename: str) -> str:
    """Derive a human-readable title from a filename."""
    name = Path(filename).stem
    return name.replace('_', ' ')


def index_pdf(filepath: str, category: str) -> dict | None:
    """Extract text from a PDF and return an index entry."""
    rel = filepath  # already relative like "medical/foo.pdf"
    title = title_from_filename(os.path.basename(filepath))
    print(f"  Processing: {rel}")
    try:
        reader = PdfReader(filepath)
    except Exception as e:
        print(f"    ERROR reading {rel}: {e}")
        return None

    pages = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            raw = page.extract_text() or ""
        except Exception:
            raw = ""
        text = clean_text(raw)
        if text:
            pages.append({"page": i, "text": text})

    print(f"    -> {len(pages)} pages extracted")
    return {
        "id": rel,
        "title": title,
        "category": category,
        "pages": pages,
    }


def index_emergency_txt(filepath: str) -> dict | None:
    """Read EMERGENCY_KNOWLEDGE.txt and split into sections on major headings."""
    print(f"  Processing: {filepath}")
    try:
        text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"    ERROR reading {filepath}: {e}")
        return None

    # Split on lines that look like major headings:
    #   all-caps lines, or lines starting with "# ", "## ", or "=== "
    heading_pattern = re.compile(
        r'^(?:'
        r'#{1,3}\s+.+'       # Markdown headings
        r'|[A-Z][A-Z _/&\-]{4,}'  # ALL-CAPS lines (5+ chars)
        r'|={3,}\s*.+\s*={3,}'    # === wrapped headings ===
        r')$',
        re.MULTILINE,
    )

    splits = list(heading_pattern.finditer(text))

    pages = []
    if not splits:
        # No headings found -- treat the whole file as one section
        cleaned = clean_text(text)
        if cleaned:
            pages.append({"page": 1, "text": cleaned})
    else:
        for idx, match in enumerate(splits):
            start = match.start()
            end = splits[idx + 1].start() if idx + 1 < len(splits) else len(text)
            section_text = clean_text(text[start:end])
            if section_text:
                pages.append({"page": idx + 1, "text": section_text})

    print(f"    -> {len(pages)} sections extracted")
    return {
        "id": "EMERGENCY_KNOWLEDGE.txt",
        "title": "Emergency Knowledge",
        "category": "emergency",
        "pages": pages,
    }


def main():
    index = []

    # Scan medical, survival, and library subdirectories
    scan_dirs = [("medical", "medical"), ("survival", "survival")]

    # Add library subdirectories
    lib_path = Path("library")
    if lib_path.is_dir():
        for sub in sorted(lib_path.iterdir()):
            if sub.is_dir() and not sub.name.startswith('.'):
                cat = sub.name.replace('-', ' ').replace('_', ' ').title()
                scan_dirs.append((cat, str(sub)))

    for category, directory in scan_dirs:
        print(f"\nScanning {directory}/...")
        dir_path = Path(directory)
        if not dir_path.is_dir():
            print(f"  WARNING: {directory}/ not found, skipping.")
            continue
        pdfs = sorted(dir_path.rglob("*.pdf"))
        print(f"  Found {len(pdfs)} PDFs")
        for pdf in pdfs:
            entry = index_pdf(str(pdf), category)
            if entry:
                index.append(entry)

    # EMERGENCY_KNOWLEDGE.txt
    print("\nProcessing EMERGENCY_KNOWLEDGE.txt...")
    ek_path = "EMERGENCY_KNOWLEDGE.txt"
    if os.path.isfile(ek_path):
        entry = index_emergency_txt(ek_path)
        if entry:
            index.append(entry)
    else:
        print(f"  WARNING: {ek_path} not found, skipping.")

    # Write output
    out_path = "medical_index.json"
    print(f"\nWriting {out_path}...")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    size_bytes = os.path.getsize(out_path)
    if size_bytes >= 1_048_576:
        size_str = f"{size_bytes / 1_048_576:.1f} MB"
    elif size_bytes >= 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes} bytes"

    print(f"\nDone! {len(index)} documents indexed.")
    print(f"Output: {out_path} ({size_str})")


if __name__ == "__main__":
    main()
