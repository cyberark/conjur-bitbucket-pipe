#!/usr/bin/env bash
set -euo pipefail

# The following is used to:
# Publish images on pre-release and tag as edge
# Promote pre-releases to releases and tag as latest

. bin/build_utils

function print_help() {
  echo "Build Usage: $0 --internal"
  echo "Release Usage: $0 --edge"
  echo "Promote Usage: $0 --promote --source <VERSION> --target <VERSION>"
  echo " --internal: publish images to registry.tld"
  echo " --edge: publish docker images to docker hub"
  echo " --source <VERSION>: specify version number of local image"
  echo " --target <VERSION>: specify version number of remote image"
}

# Fail if no arguments are given.
if [[ $# -lt 1 ]]; then
  print_help
  exit 1
fi

PUBLISH_INTERNAL=false
PUBLISH_EDGE=false
PROMOTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
  --internal)
    PUBLISH_INTERNAL=true
    ;;
  --edge)
    PUBLISH_EDGE=true
    ;;
  --promote)
    PROMOTE=true
    ;;
  --source)
    SOURCE_ARG="$2"
    shift
    ;;
  --target)
    TARGET_ARG="$2"
    shift
    ;;
  --help)
    print_help
    exit 1
    ;;
  *)
    echo "Unknown option: ${1}"
    print_help
    exit 1
    ;;
  esac
  shift
done

readonly IMAGE_NAME="conjur-bitbucket-pipe"
readonly REGISTRY='cyberark'
readonly LOCAL_REGISTRY='registry.tld'
# Version derived from CHANGLEOG and automated release library
VERSION=$(<VERSION)
readonly VERSION
FULL_VERSION_TAG="$VERSION-$(git_tag)"
readonly FULL_VERSION_TAG

if [[ ${PUBLISH_INTERNAL} = true ]]; then
  echo "Publishing built images internally to registry.tld."
  SOURCE_TAG=$FULL_VERSION_TAG
  REMOTE_TAG=$VERSION

  tag_and_push "${IMAGE_NAME}:${SOURCE_TAG}" "${LOCAL_REGISTRY}/${IMAGE_NAME}:${REMOTE_TAG}" true
  tag_and_push "${IMAGE_NAME}:${SOURCE_TAG}" "$REGISTRY/$IMAGE_NAME:edge" true
fi

if [[ ${PUBLISH_EDGE} = true ]]; then
  echo "Performing edge release."
  SOURCE_TAG=$FULL_VERSION_TAG
  REMOTE_TAG=edge
  readonly TAGS=(
    "$VERSION"
    "$REMOTE_TAG"
  )

  for tag in "${TAGS[@]}"; do
    tag_and_push "$IMAGE_NAME:$SOURCE_TAG" "$LOCAL_REGISTRY/$IMAGE_NAME:$tag"
  done
fi

if [[ ${PROMOTE} = true ]]; then
  if [[ -z ${SOURCE_ARG:-} || -z ${TARGET_ARG:-} ]]; then
  echo "When promoting, --source and --target flags are required."
  print_help
  exit 1
  fi

  # Update vars to utilize build_utils
  SOURCE_TAG=$SOURCE_ARG
  REMOTE_TAG=$TARGET_ARG

  echo "Promoting image to $REMOTE_TAG"
  readonly TAGS=(
    "$REMOTE_TAG"
    "latest"
    "edge"
  )

  # Publish images to docker hub
  for tag in "${TAGS[@]}" $(gen_versions "$REMOTE_TAG"); do
    echo "Tagging and pushing $REGISTRY/$IMAGE_NAME:$tag"
    tag_and_push "${LOCAL_REGISTRY}/$IMAGE_NAME:$SOURCE_TAG" "$REGISTRY/$IMAGE_NAME:$tag"
  done

fi
