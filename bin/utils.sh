#!/usr/bin/env bash

export compose_file="../docker-compose.yml"

function announce() {
    echo "
    ================================
     ${1}
    ================================
    "
}

function teardown {
  docker-compose down -v
  docker-compose down --remove-orphans
}
