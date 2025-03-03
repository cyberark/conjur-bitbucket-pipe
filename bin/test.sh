#!/usr/bin/env bash
set -euo pipefail

pip install -r test/requirements.txt
pytest -v test/test.py
# TODO: Coverage w/ pytest-cov
