#!/bin/bash -ex

. ./utils.sh

trap teardown ERR

USE_MOCK_JWT_SERVER=false

print_help() {
  cat << EOF
Starts a Conjur environment for development of the pipe.

Usage: start [options]
    --mock       Starts with a mock JWT server. This allows you to test
                 the pipeline without needing to run a Bitbucket pipeline.
    -h, --help   Shows this help message.
EOF
  exit
}

parse_options() {
  while true ; do
    case "$1" in
      -h | --help ) print_help ; shift ;;
      --mock ) USE_MOCK_JWT_SERVER=true ; shift ;;
       * )
         if [ -z "$1" ]; then
           break
         else
           echo "$1 is not a valid option"
           exit 1
         fi ;;
    esac
  done
}

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

  if $USE_MOCK_JWT_SERVER; then
    docker-compose up -d mock-jwt-server
  fi

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
  docker-compose exec cli conjur variable set -i bitbucket-pipelines/secret1 -v "SuperSecret"
  docker-compose exec cli conjur variable set -i bitbucket-pipelines/secret2 -v "AnotherSecret"
  docker-compose exec cli conjur variable set -i bitbucket-pipelines/myvar -v "Test value"

  # Set the Bitbucket OIDC provider configuration
  docker-compose exec cli conjur variable set -i conjur/authn-jwt/bitbucket/token-app-property -v "repositoryUuid"
  docker-compose exec cli conjur variable set -i conjur/authn-jwt/bitbucket/identity-path -v "bitbucket-pipelines"

  if $USE_MOCK_JWT_SERVER; then
    # Set the mock JWT server URL
    docker-compose exec cli conjur variable set -i conjur/authn-jwt/bitbucket/provider-uri -v "http://mock-jwt-server:8080"
  else
    # Set the Bitbucket OIDC server URL
    docker-compose exec cli conjur variable set -i conjur/authn-jwt/bitbucket/provider-uri \
      -v "https://api.bitbucket.org/2.0/workspaces/cyberark-conjur/pipelines-config/identity/oidc"
  fi
}

parse_options "$@"
main
