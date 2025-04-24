# Conjur Bitbucket Pipe

This Pipe allows you to authenticate with Conjur and retrieve secrets from
Conjur variables, and make them available as environment variables in your
Bitbucket pipelines.

## Requirements

- A Bitbucket Cloud repository with a `bitbucket-pipelines.yml` file
- Conjur Open Source, Enterprise, or Cloud

## Authenticator setup

Example policy for the Bitbucket authenticator:

```yaml

- !policy
  id: conjur/authn-jwt/bitbucket
  body:
    - !webservice
    
    - !variable provider-uri
    - !variable token-app-property
    - !variable identity-path
    
    - !group authenticatable
    - !permit
      role: !group authenticatable
      privilege: [ read, authenticate ]
      resource: !webservice

# Create a policy to contain any Bitbucket pipelines
- !policy
  id: bitbucket-pipelines
  body:
    - !group

    - &hosts
      - !host
        id: "{<bitbucket-repository-uuid>}" # Replace this with your repositoryUuid
      # Add more hosts here for other Bitbucket repositories if needed
    
    - !grant
      role: !group
      members: *hosts

    # Create some secrets for the pipelines to use
    - &variables
      - !variable secret1
      - !variable secret2
    
    # Allow the pipelines to read the variables
    - !permit
      role: !group
      privilege: [ read, execute ]
      resource: *variables

  # If using multiple Bitbucket repositories, allow each repository to read
  # only the variables it needs, to avoid exposing secrets to other repositories

# Add the pipelines to the group that can authenticate using authn-jwt/bitbucket
- !grant
  role: !group authn-jwt/bitbucket/ci/authenticatable
  members: !group bitbucket-pipelines
```

After loading this policy into Conjur, add values for the authenticator variables:

```bash
# Replace `<workspace-name>` with your Bitbucket workspace name
conjur variable set -i conjur/authn-jwt/bitbucket/provider-uri -v "https://api.bitbucket.org/2.0/workspaces/<workspace-name>/pipelines-config/identity/oidc"

conjur variable set -i conjur/authn-jwt/bitbucket/token-app-property -v "repositoryUuid"

# This is the path in the Conjur policy where the Bitbucket pipeline hosts are defined
conjur variable set -i conjur/authn-jwt/bitbucket/identity-path -v "bitbucket-pipelines"
```

## Usage

To use this Pipe in your Bitbucket pipeline, add the following to the
`bitbucket-pipelines.yml` file:

```yaml

- step:
  name: 'Retrieve secrets from Conjur'
  oidc: true # This instructs Bitbucket to use provide OIDC credentials to the Pipe
  script:
    - pipe: docker://cyberark/conjur-bitbucket-pipe:edge # TODO: This will change when the Pipe is published
      variables:
        CONJUR_URL: 'https://<your-conjur-url>'
        CONJUR_ACCOUNT: '<your-conjur-account>'
        CONJUR_SERVICE_ID: 'bitbucket' # Service ID of the JWT Authenticator in Conjur
        SECRETS: 'bitbucket-pipelines/secret1,bitbucket-pipelines/secret2' # Comma-separated list of Conjur variable IDs

```

When this step is run, the Pipe will authenticate with Conjur using the OIDC
credentials provided by Bitbucket, and retrieve the secrets specified in the
`SECRETS` variable. The secrets will be written to the pipeline's shared storage
directory, and can be accessed in subsequent steps as follows:

```yaml

- step:
  name: 'Load secrets'
  script:
    - cd /opt/atlassian/pipelines/agent/build/.bitbucket/pipelines/generated/pipeline/pipes/cyberark/conjur-bitbucket-pipe
    - set -o allexport
    - . ./load_secrets.sh

```

The secrets will now be available as environment variables in the pipeline. For
example, if you have a secret with the ID `name/of/secret1`, you can access it
in your pipeline as the environment variable `secret1`.

## Advanced Usage

When the Pipe runs, it creates two files in the pipeline's shared storage
directory: `load_secrets.sh` and `secrets.env`. The `secrets.env` file contains
the secrets as key-value pairs, and can be used directly by scripts and
applications that make use of the .env ("dotenv") file format. The
`load_secrets.sh` script is provided as a convenience to load the secrets from
the `secrets.env` file into the shell environment. It also deletes the
`secrets.env` file after loading the secrets, to prevent it from being read
again by subsequent steps.

## Limitations

- The Pipe only supports OIDC authentication with Conjur. API key authentication
  is not supported.
- Secrets are written to the pipeline's shared storage directory, which is
  accessible to all steps in the pipeline. Be careful not to expose secrets to
  unauthorized processes.
- Conjur variable names will be converted to environment variable names by
  removing any paths and using only the last component of the variable name. For
  example, a variable with the ID `name/of/secret1` will be available as the
  environment variable `secret1`. If multiple variables have the same last
  component, an error will occur.
- Due to the use of the `.env` file format, secrets with special characters
  other than `_` are not supported and will produce an error, and variable
  names cannot start with a number.

## Contributing

We welcome contributions of all kinds to this repository. For instructions on how to get started and descriptions of our
development workflows, please see our [contributing guide](CONTRIBUTING.md).

## Support

Please open an issue in this repository for any questions or issues you may have. For general support, please visit the [CyberArk Commons](https://discuss.cyberarkcommons.org/) forum.

## License

Copyright (c) 2025 CyberArk Software Ltd. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "
AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

For the full license text see [`LICENSE`](LICENSE).
