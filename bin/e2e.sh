#!/bin/bash

function testSecretsProvided() {
    echo "Testing if secrets are provided correctly..."

    declare -A expected_env_vars=(
        ["secret1"]="SuperSecret"
        ["secret2"]="AnotherSecret"
        ["myvar"]="Test value"
    )

    for var in "${!expected_env_vars[@]}"; do
        if [[ "${!var}" != "${expected_env_vars[$var]}" ]]; then
            echo "Error: Environment variable $var does not match expected value."
            exit 1
        fi
    done

}

function testSecretsFileDeleted() {
    echo "Testing if secrets.env file is deleted..."

    if [[ -f "/opt/atlassian/pipelines/agent/build/.bitbucket/pipelines/generated/pipeline/pipes/cyberark/conjur-bitbucket-pipe/secrets.env" ]]; then
        echo "Error: secrets.env file was not deleted."
        exit 1
    fi
}

echo "Running tests..."
testSecretsProvided
testSecretsFileDeleted
echo "All tests passed!"
