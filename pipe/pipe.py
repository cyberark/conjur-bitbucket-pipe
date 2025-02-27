import asyncio
import os

from bitbucket_pipes_toolkit import Pipe, get_logger
from conjur_api import Client
from conjur_api.models import ConjurConnectionInfo, CredentialsData
from conjur_api.providers import (AuthnAuthenticationStrategy,
                                  JWTAuthenticationStrategy,
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


class ConjurPipe(Pipe):
    async def run(self):
        super().run()

        logger.info('Executing the pipe...')

        conjur_url = self.get_variable('CONJUR_URL')
        account = self.get_variable('CONJUR_ACCOUNT')
        # service_id = self.get_variable('CONJUR_SERVICE_ID')
        # oidc_token = self.get_variable('BITBUCKET_STEP_OIDC_TOKEN')
        # connection_info = ConjurConnectionInfo(conjur_url=conjur_url, account=account, service_id=service_id)
        # authn_jwt_provider = JWTAuthenticationStrategy(oidc_token)

        host_id = self.get_variable('CONJUR_AUTHN_LOGIN')
        api_key = self.get_variable('CONJUR_API_KEY')
        connection_info = ConjurConnectionInfo(conjur_url=conjur_url, account=account)
        
        credentials = CredentialsData(username=host_id, password=api_key, machine=conjur_url)
        credentials_provider = SimpleCredentialsProvider()
        credentials_provider.save(credentials)
        del credentials

        client = Client(connection_info, authn_strategy=AuthnAuthenticationStrategy(credentials_provider))
        await client.login()
        
        secrets = self.get_variable('SECRETS')
        secret_list = secrets.split(',')
        secrets = await client.get_many(*secret_list)
        self.writeSecrets(secrets)

        self.success(message="Success!")

    def writeSecrets(self, secrets):
        dir = self.get_variable('BITBUCKET_PIPE_SHARED_STORAGE_DIR')
        if dir is None:
            dir = os.getcwd()
        
        logger.info(f'Writing secrets to {dir}/secrets.txt')
        
        with open(f'{dir}/secrets.txt', 'w') as f:
            for key in secrets:
                f.write(f'{key}: {secrets[key]}\n')

if __name__ == '__main__':
    pipe = ConjurPipe(pipe_metadata='/pipe.yml', schema=schema)
    asyncio.run(pipe.run())
