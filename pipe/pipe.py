import asyncio
import json
import os
import re
from dataclasses import dataclass
from typing import List

from bitbucket_pipes_toolkit import Pipe, get_logger
from conjur_api import Client
from conjur_api.models import ConjurConnectionInfo, CredentialsData
from conjur_api.providers import (JWTAuthenticationStrategy,
                                  SimpleCredentialsProvider)

logger = get_logger()

schema = {
  'CONJUR_URL': { 'type': 'string', 'required': True },
  'CONJUR_ACCOUNT': { 'type': 'string', 'required': True },
  'CONJUR_SERVICE_ID': { 'type': 'string', 'required': True },
  'BITBUCKET_STEP_OIDC_TOKEN': { 'type': 'string', 'required': True },
  'SECRETS': { 'type': 'string', 'required': True },
}

activate_script = """
#!/usr/bin/env sh
set -a
source ./secrets.env
rm ./secrets.env
set +a
"""

@dataclass
class PipeConfig:
  conjur_url: str
  conjur_account: str
  secrets: List[str]
  conjur_service_id: str
  jwt: str
  bitbucket_pipe_shared_storage_dir: str = None

  @staticmethod
  def secrets_to_list(secrets: str) -> List[str]:
    # Remove any empty strings from the list
    return list(filter(None, secrets.split(',')))

  @staticmethod
  def fetch_config_from_env():
    return PipeConfig(
      conjur_url=os.getenv('CONJUR_URL'),
      conjur_account=os.getenv('CONJUR_ACCOUNT'),
      conjur_service_id=os.getenv('CONJUR_SERVICE_ID'),
      secrets=PipeConfig.secrets_to_list(os.getenv('SECRETS')),
      jwt=os.getenv('BITBUCKET_STEP_OIDC_TOKEN'),
      bitbucket_pipe_shared_storage_dir=os.getenv('BITBUCKET_PIPE_SHARED_STORAGE_DIR')
    )

class ConjurPipe(Pipe):
  async def run(self):
    super().run()

    logger.info('Executing the pipe...')

    config = PipeConfig.fetch_config_from_env()
    client = ConjurPipe.create_conjur_client(config)
    await client.authenticate()
    
    secrets = await ConjurPipe.fetch_secrets(client, config.secrets)
    ConjurPipe.writeSecrets(secrets, config.bitbucket_pipe_shared_storage_dir)

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
    ConjurPipe.validateSecretNames(secrets)

    return await client.get_many(*secrets)

  @staticmethod
  def writeSecrets(secrets: dict, dir: str = None):
    if dir is None:
      dir = os.getcwd()
    
    logger.info(f'Writing secrets to {dir}/secrets.env')
    
    def opener_private(path, flags):
      return os.open(path, flags, 0o644)

    # The activate script needs to be executable
    def opener_executable(path, flags):
      return os.open(path, flags, 0o755)

    with open(f'{dir}/secrets.env', 'w', opener=opener_private) as f:
      for key in secrets:
        # Use `json.dumps` to surround the value with quotes and escape any quotes within the value
        value = json.dumps(secrets[key])
        # Use only the final portion of the key as the environment variable name
        key = key.split('/')[-1]
        f.write(f'{key}={value}\n')
    
    with open(f'{dir}/load_secrets.sh', 'w', opener=opener_executable) as f:
      f.write(activate_script)

  @staticmethod
  def validateSecretNames(secretNames: List[str]):
    # To set the secrets as environment variables, we need to remove any paths from the keys and
    # just use the final portion of the key as the variable name. This is because environment variables
    # cannot contain slashes. We'll also validate the resulting truncated names to ensure they are
    # valid shell variable names.
    keys = [key.split('/')[-1] for key in secretNames]

    # Ensure there are no duplicate keys, when looking just at the final portion of the key
    if len(keys) != len(set(keys)):
      raise ValueError('Duplicate secret names found in secrets list. The final portion of the key must be unique.')
    
    for key in keys:
      truncated_key = key.split('/')[-1]
      # Ensure the truncated key is a valid shell variable name
      regex = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")
      if not regex.match(truncated_key):
        raise ValueError(f'Unsupported secret name {json.dumps(truncated_key)}: variable names can only include alphanumerics and underscores, with first char being a non-digit')

if __name__ == '__main__':
  pipe = ConjurPipe(pipe_metadata='/pipe.yml', schema=schema)
  asyncio.run(pipe.run())
