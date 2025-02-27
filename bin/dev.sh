#!/usr/bin/env bash -ex

cd "$(dirname "$0")"
. ./utils.sh

docker compose down --remove-orphans

source ./start-conjur.sh

docker compose build pipe
docker compose up --no-deps -d pipe

# Start interactive container
docker exec -it \
  -e CONJUR_API_KEY \
  "$(docker compose ps -q pipe)" /bin/bash

# Now you can run:
#   python pipe.py
