#!/usr/bin/env bash -ex

cd "$(dirname "$0")"
. ./utils.sh

docker-compose down --remove-orphans

source ./start-conjur.sh

docker-compose build pipe
docker-compose up --no-deps -d pipe

# Replace this value with a valid OIDC JWT from the Bitbucket pipeline
export BITBUCKET_STEP_OIDC_TOKEN="dummy-jwt"

# Start interactive container
docker-compose exec -it \
  -e BITBUCKET_STEP_OIDC_TOKEN \
  pipe /bin/bash

# Now you can run:
#   python pipe/pipe.py
