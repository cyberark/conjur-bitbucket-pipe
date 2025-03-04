#!/usr/bin/env bash -ex

cd "$(dirname "$0")"
. ./utils.sh

docker-compose down --remove-orphans

source ./start-conjur.sh

docker-compose build pipe
docker-compose up --no-deps -d pipe

# Start interactive container
docker-compose exec -it \
  -e CONJUR_API_KEY \
  pipe /bin/bash

# Now you can run:
#   python pipe/pipe.py
