#!/bin/bash

# =========================================================
# Knowledge Archive - Double-click to start
# =========================================================

cd "$(dirname "$0")"
clear

# Stop any previous archive instance (only kill python/kiwix/llamafile processes on our ports)
for port in 9000 8080 8081; do
    lsof -ti :$port 2>/dev/null | while read pid; do
        cmd=$(ps -p "$pid" -o comm= 2>/dev/null)
        case "$cmd" in
            *python*|*kiwix*|*llamafile*) kill "$pid" 2>/dev/null ;;
        esac
    done
done
sleep 1

echo ""
echo "  Knowledge Archive"
echo "  ========================================="
echo ""

# ------- Find Python -------
PYTHON=""

# Try portable Python first
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]] && [[ -f "python_portable/python_mac_arm/python/bin/python3" ]]; then
    PYTHON="python_portable/python_mac_arm/python/bin/python3"
elif [[ "$ARCH" == "x86_64" ]] && [[ -f "python_portable/python_mac_intel/python/bin/python3" ]]; then
    PYTHON="python_portable/python_mac_intel/python/bin/python3"
fi

# Fall back to system Python
if [[ -z "$PYTHON" ]]; then
    if command -v python3 &> /dev/null; then
        PYTHON="python3"
    elif command -v python &> /dev/null; then
        PYTHON="python"
    fi
fi

if [[ -z "$PYTHON" ]]; then
    echo "  Python not found."
    echo ""
    echo "  Install Python:"
    echo "    brew install python3"
    echo "  Or run setup_portable_python.py on a machine with Python."
    echo ""
    read -p "  Press Enter to close..."
    exit 1
fi

echo "  Using: $PYTHON"
echo ""

# ------- Start -------
"$PYTHON" start_archive.py

# Keep window open on error
if [[ $? -ne 0 ]]; then
    echo ""
    echo "  Archive stopped. Check errors above."
    echo ""
    read -p "  Press Enter to close..."
fi
