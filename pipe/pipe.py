import asyncio
import os
from dataclasses import dataclass
from typing import List

from bitbucket_pipes_toolkit import Pipe, get_logger
from conjur_api import Client
from conjur_api.models import ConjurConnectionInfo, CredentialsData
from conjur_api.providers import (AuthnAuthenticationStrategy,
                                  SimpleCredentialsProvider)

logger = get_logger()

schema = {
  'CONJUR_URL': { 'type': 'string', 'required': True },
  'CONJUR_ACCOUNT': { 'type': 'string', 'required': True },
#   'CONJUR_SERVICE_ID': { 'type': 'string', 'required': True },
  'SECRETS': { 'type': 'string', 'required': True },
  'CONJUR_AUTHN_LOGIN': { 'type': 'string', 'required': True },
  'CONJUR_API_KEY': { 'type': 'string', 'required': True },
}

@dataclass
class PipeConfig:
  conjur_url: str
  conjur_account: str
  secrets: List[str]
  conjur_authn_login: str
  conjur_api_key: str
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
      secrets=PipeConfig.secrets_to_list(os.getenv('SECRETS')),
      conjur_authn_login=os.getenv('CONJUR_AUTHN_LOGIN'),
      conjur_api_key=os.getenv('CONJUR_API_KEY'),
      bitbucket_pipe_shared_storage_dir=os.getenv('BITBUCKET_PIPE_SHARED_STORAGE_DIR')
    )

class ConjurPipe(Pipe):
  async def run(self):
    super().run()

    logger.info('Executing the pipe...')

    config = PipeConfig.fetch_config_from_env()
    client = ConjurPipe.create_conjur_client(config)
    await client.login()
    
    secrets = await ConjurPipe.fetch_secrets(client, config.secrets)
    ConjurPipe.writeSecrets(secrets, config.bitbucket_pipe_shared_storage_dir)

    ConjurPipe.success(message="Success!")

  @staticmethod
  def create_conjur_client(config: PipeConfig):
    connection_info = ConjurConnectionInfo(conjur_url=config.conjur_url,
                                            account=config.conjur_account)
    credentials = CredentialsData(username=config.conjur_authn_login,
                                  password=config.conjur_api_key,
                                  machine=config.conjur_url)
    credentials_provider = SimpleCredentialsProvider()
    credentials_provider.save(credentials)
    del credentials

    client = Client(connection_info, authn_strategy=AuthnAuthenticationStrategy(credentials_provider))
    return client

  @staticmethod
  async def fetch_secrets(client: Client, secrets: List[str]):
    return await client.get_many(*secrets)

  @staticmethod
  def writeSecrets(secrets: dict, dir: str = None):
    if dir is None:
        dir = os.getcwd()
    
    logger.info(f'Writing secrets to {dir}/secrets.txt')
    
    with open(f'{dir}/secrets.txt', 'w') as f:
        for key in secrets:
            f.write(f'{key}: {secrets[key]}\n')


if __name__ == '__main__':
  pipe = ConjurPipe(pipe_metadata='/pipe.yml', schema=schema)
  asyncio.run(pipe.run())
