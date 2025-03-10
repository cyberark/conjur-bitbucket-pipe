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
  docker-compose exec cli conjur variable set -i conjur/authn-bitbucket/ci/pipelines/secret1 -v "SuperSecret"
  docker-compose exec cli conjur variable set -i conjur/authn-bitbucket/ci/pipelines/secret2 -v "AnotherSecret"

  # Set the Bitbucket OIDC provider configuration
  docker-compose exec cli conjur variable set -i conjur/authn-bitbucket/ci/provider-uri -v "https://api.bitbucket.org/2.0/workspaces/cyberark1/pipelines-config/identity/oidc"
  docker-compose exec cli conjur variable set -i conjur/authn-bitbucket/ci/token-app-property -v "repositoryUuid"
  docker-compose exec cli conjur variable set -i conjur/authn-bitbucket/ci/identity-path -v "conjur/authn-bitbucket/ci/pipelines"
}

main
