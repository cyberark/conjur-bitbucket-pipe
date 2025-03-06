import asyncio
import json
import os
from unittest import mock
from unittest.mock import patch

from aiounittest import AsyncTestCase
from conjur_api import Client
from conjur_api.providers import JWTAuthenticationStrategy

from pipe.pipe import ConjurPipe, PipeConfig


class TestPipe(AsyncTestCase):
  def test_create_conjur_client(self):
    config = PipeConfig(
      conjur_url='https://conjur.example.com',
      conjur_account='myaccount',
      conjur_service_id='bitbucket',
      jwt='jwt-content',
      secrets=[]
    )

    client = ConjurPipe.create_conjur_client(config)
    self.assertIsNotNone(client)
    self.assertIsInstance(client, Client)
    self.assertEqual(client.connection_info.conjur_url, 'https://conjur.example.com')
    self.assertEqual(client.connection_info.conjur_account, 'myaccount')
    self.assertEqual(client.connection_info.service_id, 'bitbucket')
    self.assertIsInstance(client._api.authn_strategy, JWTAuthenticationStrategy)

  async def test_fetch_secrets(self):
    # Mock the Conjur client's get_many method and test that it is called with the correct arguments
    client = mock.MagicMock(spec=Client)
    with patch.object(client, 'get_many') as mock_get_many:
      ret = asyncio.Future()
      ret.set_result({'path/secret1': 'value1', 'other/path/secret2': 'value2'})
      mock_get_many.return_value = ret
      secrets = await ConjurPipe.fetch_secrets(client, ['path/secret1', 'other/path/secret2'])
      mock_get_many.assert_called_once()
      self.assertEqual(secrets, {'path/secret1': 'value1', 'other/path/secret2': 'value2'})

  async def test_fetch_secrets_duplicate_secret_names(self):
    duplicate_secret_names = [
      'path/secret1',
      'other/path/secret1',
    ]

    client = mock.MagicMock(spec=Client)
    with patch.object(client, 'get_many') as mock_get_many:
      with self.assertRaises(ValueError) as err:
        await ConjurPipe.fetch_secrets(client, duplicate_secret_names)
      self.assertIn("Duplicate secret names", str(err.exception))
      
      mock_get_many.assert_not_called()

  async def test_fetch_secrets_invalid_secret_names(self):
    invalid_secret_names = [
      'contains spaces',
      '8numeric',
      'quote"char"',
      '<special>chars',
      'trailing_space ',
      ' leading_space',
      'equal=sign',
      'dollar$sign',
      'hypen-sign',
    ]

    client = mock.MagicMock(spec=Client)
    with patch.object(client, 'get_many') as mock_get_many:
      for secret_name in invalid_secret_names:
        with self.assertRaises(ValueError) as err:
          await ConjurPipe.fetch_secrets(client, [secret_name])
        self.assertIn("Unsupported secret name " + json.dumps(secret_name), str(err.exception))
      
      mock_get_many.assert_not_called()
    
    # TODO: Test failure cases

  def test_write_secrets(self):
    # Create a dictionary of secrets with some special characters
    secrets = {
      'secret1': 'value 1',
      'secret2': 'value=2',
      'secret3': 'value"3',
      'path/secret4': 'value\'4' # "path/" will be removed from the key
    }
    # Mock the logger and test that it is called with the correct arguments
    with patch('pipe.pipe.logger') as mock_logger:
      ConjurPipe.writeSecrets(secrets, '/tmp')
      mock_logger.info.assert_called_once_with('Writing secrets to /tmp/secrets.env')

    # Test default dir
    with patch('pipe.pipe.logger') as mock_logger:
      ConjurPipe.writeSecrets(secrets)
      mock_logger.info.assert_called_once_with(f'Writing secrets to {os.getcwd()}/secrets.env')

    # Check that the file is written correctly
    with open('secrets.env', 'r') as f: content = f.read()
    self.assertEqual(content, """secret1="value 1"
secret2="value=2"
secret3="value\\"3"
secret4="value\'4"
""")
    
    # Check that the load_secrets.sh script is written correctly
    with open('load_secrets.sh', 'r') as f: content = f.read()
    self.assertIn('source ./secrets.env', content)
    self.assertIn('rm ./secrets.env', content)

    # Clean up
    os.remove('secrets.env')
    os.remove('load_secrets.sh')

  # TODO: Variable values with special characters and quotes
  # TODO: Test failure cases

