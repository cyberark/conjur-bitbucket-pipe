import asyncio
import json
import os
import re
from dataclasses import dataclass
from typing import List

from bitbucket_pipes_toolkit import Pipe, get_logger
from conjur_api import Client
from conjur_api.models import ConjurConnectionInfo
from conjur_api.providers import JWTAuthenticationStrategy

DEFAULT_CONJUR_ACCOUNT = 'conjur'
DEFAULT_CONJUR_SERVICE_ID = 'bitbucket'

logger = get_logger()

schema = {
    'CONJUR_URL': { 'type': 'string', 'required': True },
    'CONJUR_ACCOUNT': { 'type': 'string', 'required': True, 'default': DEFAULT_CONJUR_ACCOUNT },
    'CONJUR_SERVICE_ID': { 'type': 'string', 'required': True, 'default': DEFAULT_CONJUR_SERVICE_ID },
    'BITBUCKET_STEP_OIDC_TOKEN': { 'type': 'string', 'required': True },
    'SECRETS': { 'type': 'string', 'required': True },
}

DEFAULT_OUTPUT_DIR = os.path.join('.secrets')

ACTIVATE_SCRIPT = """
#!/usr/bin/env bash
set -a
file="{output_dir}/secrets.env"
source "$file"
rm "$file"
set +a
"""

@dataclass
class PipeConfig:
    conjur_url: str
    conjur_account: str
    secrets: List[str]
    conjur_service_id: str
    jwt: str
    output_dir: str = DEFAULT_OUTPUT_DIR

    @staticmethod
    def secrets_to_list(secrets: str) -> List[str]:
        # Remove any empty strings from the list
        return list(filter(None, secrets.split(',')))

    @staticmethod
    def get_default_conjur_account():
        logger.info('No CONJUR_ACCOUNT provided, using default value "conjur"')
        return DEFAULT_CONJUR_ACCOUNT

    @staticmethod
    def get_default_service_id():
        logger.info('No CONJUR_SERVICE_ID provided, using default value "bitbucket"')
        return DEFAULT_CONJUR_SERVICE_ID

    @staticmethod
    def fetch_config_from_env():
        return PipeConfig(
            conjur_url=os.getenv('CONJUR_URL'),
            conjur_account=os.getenv('CONJUR_ACCOUNT') or PipeConfig.get_default_conjur_account(),
            conjur_service_id=os.getenv('CONJUR_SERVICE_ID') or PipeConfig.get_default_service_id(),
            secrets=PipeConfig.secrets_to_list(os.getenv('SECRETS')),
            jwt=os.getenv('BITBUCKET_STEP_OIDC_TOKEN'),
        )

class ConjurPipe(Pipe):
    async def run(self):
        super().run()

        logger.info('Executing Conjur pipe...')

        config = PipeConfig.fetch_config_from_env()
        client = ConjurPipe.create_conjur_client(config)
        await client.authenticate()

        secrets = await ConjurPipe.fetch_secrets(client, config.secrets)
        ConjurPipe.write_secrets(secrets, config.output_dir)

        ConjurPipe.success(message="Success!")

    @staticmethod
    def create_conjur_client(config: PipeConfig):
        connection_info = ConjurConnectionInfo(conjur_url=config.conjur_url,
                                               account=config.conjur_account,
                                               service_id=config.conjur_service_id)

        client = Client(connection_info, authn_strategy=JWTAuthenticationStrategy(config.jwt))
        return client

    @staticmethod
    async def fetch_secrets(client: Client, secrets: List[str]):
        # Before fetching, ensure the variable names are valid to be used as environment variables
        ConjurPipe.validate_secret_names(secrets)

        return await client.get_many(*secrets)

    @staticmethod
    def write_secrets(secrets: dict, outdir: str = None):
        if outdir is None:
            outdir = DEFAULT_OUTPUT_DIR

        # Create the output directory if it doesn't exist
        if not os.path.exists(outdir):
            os.makedirs(outdir, 0o700)

        logger.info(f'Writing secrets to {outdir}/secrets.env')

        def opener_private(path, flags):
            return os.open(path, flags, 0o600)

        # The activate script needs to be executable
        def opener_executable(path, flags):
            return os.open(path, flags, 0o700)

        with open(f'{outdir}/secrets.env', 'w', encoding='utf-8', opener=opener_private) as file:
            for key in secrets:
                # Use `json.dumps` to surround the value with quotes and escape any quotes within the value
                value = json.dumps(secrets[key])
                # Use only the final portion of the key as the environment variable name
                key = key.split('/')[-1]
                file.write(f'{key}={value}\n')

        with open(f'{outdir}/load_secrets.sh', 'w', encoding='utf-8', opener=opener_executable) as file:
            file.write(ACTIVATE_SCRIPT.format(output_dir=outdir))

    @staticmethod
    def validate_secret_names(secret_names: List[str]):
        # To set the secrets as environment variables, we need to remove any paths from the keys and
        # just use the final portion of the key as the variable name. This is because environment variables
        # cannot contain slashes. We'll also validate the resulting truncated names to ensure they are
        # valid shell variable names.
        keys = [key.split('/')[-1] for key in secret_names]

        # Ensure there are no duplicate keys, when looking just at the final portion of the key
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate secret names found in secrets list. The final portion of the key must be unique.')

        for key in keys:
            truncated_key = key.split('/')[-1]
            # Ensure the truncated key is a valid shell variable name
            regex = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")
            if not regex.match(truncated_key):
                raise ValueError(f'Unsupported secret name {json.dumps(truncated_key)}: variable names can only include alphanumerics" + \
                                 "and underscores, with first char being a non-digit')

if __name__ == '__main__':
    pipe = ConjurPipe(pipe_metadata='/pipe.yml', schema=schema)
    asyncio.run(pipe.run())
