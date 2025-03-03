#!/usr/bin/env bash
set -euo pipefail

# go to repo root folder for execution
cd $(dirname $0)/..

. bin/build_utils

VERSION=unreleased
# Version derived from CHANGELOG and automated release library
[ -f VERSION ] && VERSION=$(<VERSION)
FULL_VERSION_TAG="$VERSION-$(git_tag)"

echo "---"

function main() {
  build_docker_image
}

function build_docker_image() {

  echo "Building conjur-bitbucket-pipe:$FULL_VERSION_TAG Docker image"

  docker build \
      --build-arg TAG=$(git_tag) \
      --tag "conjur-bitbucket-pipe:dev" \
      --tag "conjur-bitbucket-pipe:${FULL_VERSION_TAG}" \
      --tag "conjur-bitbucket-pipe:latest" \
      .

  echo "---"

}

main
