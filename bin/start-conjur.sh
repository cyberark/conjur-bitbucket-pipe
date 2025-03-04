#!/bin/bash -ex

. ./utils.sh

trap teardown ERR

announce "Compose Project Name: $COMPOSE_PROJECT_NAME"

main() {
  announce "Pulling images..."
  docker-compose pull "conjur" "postgres"
  echo "Done!"

  announce "Building images..."
  docker-compose build "conjur" "postgres"
  echo "Done!"

  announce "Starting Conjur environment..."
  export CONJUR_DATA_KEY="$(docker-compose run -T --no-deps conjur data-key generate)"
  docker-compose up --no-deps -d "conjur" "postgres"
  echo "Done!"

  announce "Waiting for conjur to start..."
  docker-compose exec conjur conjurctl wait

  echo "Done!"

  # Log in to the CLI so we can load policy and set variables
  admin_api_key=$(docker-compose exec conjur conjurctl role retrieve-key conjur:user:admin | tr -d '\r')

  docker-compose up -d cli
  docker-compose exec cli conjur login -i admin -p "$admin_api_key"
  docker-compose cp policy.yml cli:/policy.yml
  docker-compose exec cli conjur policy load -b root -f /policy.yml
  docker-compose exec cli conjur variable set -i secret1 -v "SuperSecret"
  docker-compose exec cli conjur variable set -i secret2 -v "AnotherSecret"

  # Export Pipe API key
  pipe_api_key=$(docker-compose exec conjur conjurctl role retrieve-key conjur:host:pipe | tr -d '\r')
  export CONJUR_API_KEY="$pipe_api_key"
}

main
