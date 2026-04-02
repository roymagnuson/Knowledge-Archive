#!/usr/bin/env python3
"""
Emergency Knowledge Archive — Medical & Survival PDF Downloader
================================================================
Downloads free, legally available medical and survival PDFs from:
  - Hesperian Health Guides (chapter PDFs from hesperian.org)
  - Internet Archive (public domain / freely shared editions)
  - WHO / ICRC (official open-access publications)
  - CDC / EPA (US government, public domain)

Run from your EmergencyKnowledge folder:
    python3 download_medical_survival.py

All content is either public domain, Creative Commons, or explicitly
provided free for download by the publishers.
"""

import os
import sys
import time
import hashlib
import subprocess
from pathlib import Path

REQUIRED_DEPS = ['requests', 'tqdm']

def check_dependencies():
    """Check if required dependencies are installed, prompt to install if missing."""
    missing = []
    for dep in REQUIRED_DEPS:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    if missing:
        print(f"\n  Missing dependencies: {', '.join(missing)}")
        response = input("  Install them now? [Y/n] ").strip().lower()
        if response and response != 'y':
            print(f"  Install manually: pip install {' '.join(missing)}")
            sys.exit(1)
        for dep in missing:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', dep, '-q'],
                stdout=subprocess.DEVNULL
            )

check_dependencies()

import requests
from tqdm import tqdm

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────
DELAY_BETWEEN_DOWNLOADS = 2  # seconds, be polite to servers
TIMEOUT = 120
MAX_RETRIES = 3
USER_AGENT = 'EmergencyArchive/1.0 (Personal archival use)'

# ─────────────────────────────────────────────────────────────
# DOWNLOAD MANIFEST
# Each entry: { name, filename, category, urls[], size_hint, desc }
# Multiple URLs = fallback mirrors
# ─────────────────────────────────────────────────────────────

DOWNLOADS = [
    # ═══════════════════════════════════════════════════════════
    # MEDICAL — Hesperian Health Guides
    # ═══════════════════════════════════════════════════════════
    {
        "name": "Where There Is No Doctor (2024 edition)",
        "filename": "Where_There_Is_No_Doctor.pdf",
        "category": "medical",
        "desc": "The world's most widely-used primary health care manual.",
        "size_hint": "~20 MB",
        "urls": [
            "https://ia601902.us.archive.org/24/items/WhereThereIsNoDoctor-English-DavidWerner/14.DavidWerner-WhereThereIsNoDoctor.pdf",
            "https://hesperian.org/wp-content/uploads/pdf/en_wtnd_2022/en_wtnd_2022_full_book.pdf",
        ],
    },
    {
        "name": "Where There Is No Dentist",
        "filename": "Where_There_Is_No_Dentist.pdf",
        "category": "medical",
        "desc": "Dental care guide for when professional help isn't available.",
        "size_hint": "~10 MB",
        "urls": [
            "https://ia800301.us.archive.org/14/items/WhereThereIsNoDentist/WhereThereIsNoDentist.pdf",
            "https://hesperian.org/wp-content/uploads/pdf/en_wtnd_dental_2022/en_wtnd_dental_2022.pdf",
        ],
    },
    {
        "name": "A Book for Midwives",
        "filename": "A_Book_For_Midwives.pdf",
        "category": "medical",
        "desc": "Comprehensive guide to pregnancy, childbirth, and newborn care.",
        "size_hint": "~15 MB",
        "urls": [
            "https://ia800500.us.archive.org/32/items/ABookForMidwives/A%20Book%20For%20Midwives.pdf",
            "https://hesperian.org/wp-content/uploads/pdf/en_bfm_2022/en_bfm_2022.pdf",
        ],
    },
    {
        "name": "WHO First Aid Guidelines",
        "filename": "WHO_First_Aid_Manual.pdf",
        "category": "medical",
        "desc": "World Health Organization first aid recommendations.",
        "size_hint": "~5 MB",
        "urls": [
            "https://iris.who.int/bitstream/handle/10665/44458/9789241599870_eng.pdf",
            "https://apps.who.int/iris/bitstream/handle/10665/44458/9789241599870_eng.pdf",
        ],
    },
    # ═══════════════════════════════════════════════════════════
    # SURVIVAL
    # ═══════════════════════════════════════════════════════════
    {
        "name": "US Army Survival Manual FM 21-76",
        "filename": "FM_21-76_Survival_Manual.pdf",
        "category": "survival",
        "desc": "Comprehensive military survival manual covering all environments.",
        "size_hint": "~32 MB",
        "urls": [
            "https://ia800300.us.archive.org/4/items/Fm21-76SurvivalManual/FM21-76_SurvivalManual.pdf",
            "https://www.survivalschool.us/wp-content/uploads/2019/09/FM-21-76-US-ARMY-SURVIVAL-MANUAL-Searchable.pdf",
        ],
    },
]


# ─────────────────────────────────────────────────────────────
# Download helpers
# ─────────────────────────────────────────────────────────────

def get_session():
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    return session


def download_file(session, url, output_path, desc="Downloading"):
    """Download a file with progress bar and PDF validation."""
    try:
        response = session.get(url, stream=True, timeout=TIMEOUT)
        response.raise_for_status()

        total = int(response.headers.get('content-length', 0))

        temp_path = output_path.with_suffix(output_path.suffix + '.partial')
        with open(temp_path, 'wb') as f:
            with tqdm(total=total, unit='B', unit_scale=True, desc=desc[:40]) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))

        # Verify it's actually a PDF
        with open(temp_path, 'rb') as f:
            header = f.read(5)
            if header != b'%PDF-':
                temp_path.unlink()
                return False, "Downloaded file is not a valid PDF"

        # Move to final location
        temp_path.replace(output_path)
        return True, None
    except Exception as e:
        # Clean up partial files
        temp_path = output_path.with_suffix(output_path.suffix + '.partial')
        if temp_path.exists():
            temp_path.unlink()
        if output_path.exists():
            output_path.unlink()
        return False, str(e)


def main():
    script_dir = Path(__file__).parent.resolve()
    session = get_session()

    print()
    print("  Emergency Knowledge — Medical & Survival PDFs")
    print("  " + "=" * 50)
    print()
    print(f"  Source directory: {script_dir}")
    print(f"  Downloads: {len(DOWNLOADS)} files")
    print()

    stats = {"downloaded": 0, "skipped": 0, "failed": 0}
    current_category = None

    for item in DOWNLOADS:
        category = item["category"]
        if category != current_category:
            current_category = category
            print(f"\n  [{category.upper()}]")

        category_dir = script_dir / category
        category_dir.mkdir(exist_ok=True)

        output_path = category_dir / item["filename"]

        # Check if already exists and is valid
        if output_path.exists():
            with open(output_path, 'rb') as f:
                if f.read(5) == b'%PDF-':
                    print(f"    ✓ {item['filename']} — already exists")
                    stats["skipped"] += 1
                    continue
                else:
                    print(f"    ⚠ {item['filename']} — invalid, re-downloading...")
                    output_path.unlink()

        print(f"    Downloading {item['name']} ({item['size_hint']})...")

        success = False
        for i, url in enumerate(item["urls"]):
            if i > 0:
                print(f"      Trying mirror {i + 1}/{len(item['urls'])}...")
                time.sleep(DELAY_BETWEEN_DOWNLOADS)

            ok, error = download_file(session, url, output_path, item["filename"])
            if ok:
                print(f"    ✓ Complete: {item['filename']}")
                stats["downloaded"] += 1
                success = True
                break
            else:
                print(f"      Failed: {error[:80]}")

        if not success:
            print(f"    ✗ All mirrors failed for {item['filename']}")
            print(f"      Try downloading manually:")
            for url in item["urls"]:
                print(f"        {url}")
            stats["failed"] += 1

        time.sleep(DELAY_BETWEEN_DOWNLOADS)

    print()
    print("  " + "=" * 50)
    print(f"  Downloaded: {stats['downloaded']}  Skipped: {stats['skipped']}  Failed: {stats['failed']}")
    print()

    if stats["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
