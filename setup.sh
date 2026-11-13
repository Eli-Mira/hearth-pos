#!/bin/bash
set -e
echo "=== Installing hearth-pos ==="
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
echo "Done. Run: python main.py"
