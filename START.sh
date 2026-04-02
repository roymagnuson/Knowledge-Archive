#!/bin/bash

# Knowledge Archive Launcher
# Double-click this file to start

cd "$(dirname "$0")"

echo ""
echo "  Knowledge Archive"
echo "  ========================================="
echo ""

# Detect platform
PLATFORM="unknown"
ARCH=$(uname -m)

if [[ "$OSTYPE" == "darwin"* ]]; then
    if [[ "$ARCH" == "arm64" ]]; then
        PLATFORM="mac_arm"
    else
        PLATFORM="mac_intel"
    fi
elif [[ "$OSTYPE" == "linux"* ]]; then
    PLATFORM="linux"
fi

# Try portable Python first
PORTABLE_PYTHON=""
if [[ "$PLATFORM" == "mac_arm" ]] && [[ -f "python_portable/python_mac_arm/python/bin/python3" ]]; then
    PORTABLE_PYTHON="python_portable/python_mac_arm/python/bin/python3"
elif [[ "$PLATFORM" == "mac_intel" ]] && [[ -f "python_portable/python_mac_intel/python/bin/python3" ]]; then
    PORTABLE_PYTHON="python_portable/python_mac_intel/python/bin/python3"
elif [[ "$PLATFORM" == "linux" ]] && [[ -f "python_portable/python_linux/python/bin/python3" ]]; then
    PORTABLE_PYTHON="python_portable/python_linux/python/bin/python3"
fi

if [[ -n "$PORTABLE_PYTHON" ]]; then
    echo "  Using portable Python..."
    "$PORTABLE_PYTHON" START_ARCHIVE.py
    exit 0
fi

# Try system Python
if command -v python3 &> /dev/null; then
    echo "  Using system Python..."
    python3 START_ARCHIVE.py
    exit 0
fi

if command -v python &> /dev/null; then
    echo "  Using system Python..."
    python START_ARCHIVE.py
    exit 0
fi

# No Python found
echo ""
echo "  ============================================="
echo "  Python not found!"
echo ""
echo "  Option 1: Run setup_portable_python.py first"
echo "            (requires Python on another machine)"
echo ""
echo "  Option 2: Install Python:"
echo "      Mac:   brew install python3"
echo "      Linux: sudo apt install python3"
echo "  ============================================="
echo ""
read -p "  Press Enter to close..."
