#!/usr/bin/env bash

cd "$(dirname "$0")"
. ./utils.sh

docker-compose down --remove-orphans

. ./start-conjur.sh --mock

docker-compose build pipe
docker-compose up --no-deps -d pipe

# Fetch a mock JWT token
export BITBUCKET_STEP_OIDC_TOKEN=$(curl "http://localhost:8008/token")

announce "
You are now in the interactive container.
You can run the following command to test the pipe:
  python pipe/pipe.py
"

# Start interactive container
docker-compose exec -it \
  -e BITBUCKET_STEP_OIDC_TOKEN \
  pipe /bin/bash
