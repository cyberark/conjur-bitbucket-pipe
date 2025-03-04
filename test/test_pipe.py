import asyncio
import os
from unittest import mock
from unittest.mock import patch

from aiounittest import AsyncTestCase
from conjur_api import Client
from conjur_api.providers import AuthnAuthenticationStrategy

from pipe.pipe import ConjurPipe, PipeConfig


class TestPipe(AsyncTestCase):
  def test_create_conjur_client(self):
    config = PipeConfig(
      conjur_url='https://conjur.example.com',
      conjur_account='myaccount',
      conjur_authn_login='host/myhost',
      conjur_api_key='apikey',
      secrets=''
    )

    client = ConjurPipe.create_conjur_client(config)
    self.assertIsNotNone(client)
    self.assertIsInstance(client, Client)
    self.assertEqual(client.connection_info.conjur_url, 'https://conjur.example.com')
    self.assertEqual(client.connection_info.conjur_account, 'myaccount')
    self.assertIsInstance(client._api.authn_strategy, AuthnAuthenticationStrategy)

  async def test_fetch_secrets(self):
    # Mock the Conjur client's get_many method and test that it is called with the correct arguments
    client = mock.MagicMock(spec=Client)
    with patch.object(client, 'get_many') as mock_get_many:
      ret = asyncio.Future()
      ret.set_result({'secret1': 'value1', 'secret2': 'value2'})
      mock_get_many.return_value = ret
      secrets = await ConjurPipe.fetch_secrets(client, ['secret1', 'secret2'])
      mock_get_many.assert_called_once()
      self.assertEqual(secrets, {'secret1': 'value1', 'secret2': 'value2'})
    
    # TODO: Test failure cases

  def test_write_secrets(self):
    secrets = {'secret1': 'value1', 'secret2': 'value2'}
    # Mock the logger and test that it is called with the correct arguments
    with patch('pipe.pipe.logger') as mock_logger:
      ConjurPipe.writeSecrets(secrets, '/tmp')
      mock_logger.info.assert_called_once_with('Writing secrets to /tmp/secrets.txt')

    # Test default dir
    with patch('pipe.pipe.logger') as mock_logger:
      ConjurPipe.writeSecrets(secrets)
      mock_logger.info.assert_called_once_with(f'Writing secrets to {os.getcwd()}/secrets.txt')

    # Check that the file is written correctly
    with open('secrets.txt', 'r') as f: content = f.read()
    self.assertEqual(content, 'secret1: value1\nsecret2: value2\n')

    # Clean up
    os.remove('secrets.txt')

    # TODO: Test failure cases

