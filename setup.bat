@echo off
echo === Installing hearth-pos ===
python -m venv .venv
.venv\Scripts\activate
pip install -e .
echo Done. Run: python main.py
