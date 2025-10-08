#!/usr/bin/env bash
set -euo pipefail

test_script="
pip install -r requirements.txt --root-user-action ignore
coverage run -m unittest && coverage xml
"

# Run tests and coverage in a Docker container
docker run --rm \
  -t \
  -v "$(pwd):/tests" \
  -w /tests \
  python:3.13-slim \
    bash -c "$test_script"
