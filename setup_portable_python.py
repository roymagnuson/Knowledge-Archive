#!/usr/bin/env python3
"""
Portable Python Setup Script

Downloads and configures portable Python distributions so the archive
works without requiring Python to be installed on the system.

Run this ONCE after downloading all the content:
    python setup_portable_python.py

This creates a 'python_portable' folder with Python for Windows, Mac, and Linux.
The START launchers will automatically use it.
"""

import os
import sys
import platform
import subprocess
import shutil
import tarfile
import zipfile
from pathlib import Path

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests', 'tqdm', '-q'])
    import requests
    from tqdm import tqdm

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
PORTABLE_DIR = SCRIPT_DIR / 'python_portable'

# Python standalone builds from python-build-standalone (by Astral/indygreg)
# These are fully self-contained Python distributions
# https://github.com/astral-sh/python-build-standalone/releases

PYTHON_VERSION = "3.11.9"
RELEASE_TAG = "20240814"

DOWNLOADS = {
    'windows': {
        'url': f'https://github.com/astral-sh/python-build-standalone/releases/download/{RELEASE_TAG}/cpython-{PYTHON_VERSION}+{RELEASE_TAG}-x86_64-pc-windows-msvc-shared-install_only_stripped.tar.gz',
        'dirname': 'python_windows',
        'python_path': 'python/python.exe',
    },
    'mac_intel': {
        'url': f'https://github.com/astral-sh/python-build-standalone/releases/download/{RELEASE_TAG}/cpython-{PYTHON_VERSION}+{RELEASE_TAG}-x86_64-apple-darwin-install_only_stripped.tar.gz',
        'dirname': 'python_mac_intel',
        'python_path': 'python/bin/python3',
    },
    'mac_arm': {
        'url': f'https://github.com/astral-sh/python-build-standalone/releases/download/{RELEASE_TAG}/cpython-{PYTHON_VERSION}+{RELEASE_TAG}-aarch64-apple-darwin-install_only_stripped.tar.gz',
        'dirname': 'python_mac_arm',
        'python_path': 'python/bin/python3',
    },
    'linux': {
        'url': f'https://github.com/astral-sh/python-build-standalone/releases/download/{RELEASE_TAG}/cpython-{PYTHON_VERSION}+{RELEASE_TAG}-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz',
        'dirname': 'python_linux',
        'python_path': 'python/bin/python3',
    },
}

# =============================================================================
# HELPERS
# =============================================================================

def download_file(url, output_path):
    """Download with progress bar."""
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    
    total = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as f:
        with tqdm(total=total, unit='B', unit_scale=True, desc=output_path.name) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))


def extract_tarball(tar_path, output_dir):
    """Extract a tar.gz file."""
    print(f"  Extracting to {output_dir.name}...")
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(output_dir)


def main():
    print()
    print("  Portable Python Setup")
    print("  " + "=" * 40)
    print()
    print("  This downloads Python for Windows, Mac, and Linux")
    print("  so the archive works without installing Python.")
    print()
    print(f"  Download size: ~300 MB")
    print(f"  Installed size: ~400 MB")
    print()
    
    response = input("  Continue? [Y/n] ").strip().lower()
    if response and response != 'y':
        print("  Aborted.")
        return
    
    PORTABLE_DIR.mkdir(exist_ok=True)
    
    for platform_name, config in DOWNLOADS.items():
        print()
        print(f"  [{platform_name}]")
        
        output_dir = PORTABLE_DIR / config['dirname']
        
        if output_dir.exists():
            print(f"    Already exists, skipping")
            continue
        
        # Download
        tar_path = PORTABLE_DIR / f"{platform_name}.tar.gz"
        
        if not tar_path.exists():
            print(f"    Downloading...")
            try:
                download_file(config['url'], tar_path)
            except Exception as e:
                print(f"    Failed: {e}")
                continue
        
        # Extract
        output_dir.mkdir(exist_ok=True)
        try:
            extract_tarball(tar_path, output_dir)
            tar_path.unlink()  # Remove archive after extraction
            print(f"    Done")
        except Exception as e:
            print(f"    Extract failed: {e}")
            continue
    
    print()
    print("  " + "=" * 40)
    print("  Portable Python setup complete!")
    print()
    print("  The START launchers will automatically use it.")
    print("  " + "=" * 40)
    print()


if __name__ == "__main__":
    main()
