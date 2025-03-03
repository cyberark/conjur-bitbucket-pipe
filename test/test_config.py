import os
import unittest
from unittest.mock import patch

from pipe.pipe import PipeConfig


class TestConfig(unittest.TestCase):

  @patch.dict(os.environ, {
    'CONJUR_URL': 'https://conjur.example.com',
    'CONJUR_ACCOUNT': 'myaccount',
    'SECRETS': 'secret1,secret2',
    'CONJUR_AUTHN_LOGIN': 'admin',
    'CONJUR_API_KEY': 'apikey',
    'BITBUCKET_PIPE_SHARED_STORAGE_DIR': '/tmp'
  })
  def test_fetch_config_from_env(self):
    config = PipeConfig.fetch_config_from_env()
    self.assertIsInstance(config, PipeConfig)
    self.assertEqual(config.conjur_url, 'https://conjur.example.com')
    self.assertEqual(config.conjur_account, 'myaccount')
    self.assertEqual(config.secrets, ['secret1','secret2'])
    self.assertEqual(config.conjur_authn_login, 'admin')
    self.assertEqual(config.conjur_api_key, 'apikey')
    self.assertEqual(config.bitbucket_pipe_shared_storage_dir, '/tmp')

  @patch.dict(os.environ, {
    'CONJUR_URL': 'https://conjur.example.com',
    'CONJUR_ACCOUNT': 'myaccount',
    'SECRETS': 'single_secret',
    'CONJUR_AUTHN_LOGIN': 'admin',
    'CONJUR_API_KEY': 'apikey'
  }, clear=True)
  def test_fetch_config_from_env_without_optional(self):
    config = PipeConfig.fetch_config_from_env()
    self.assertEqual(config.conjur_url, 'https://conjur.example.com')
    self.assertEqual(config.conjur_account, 'myaccount')
    self.assertEqual(config.secrets, ['single_secret'])
    self.assertEqual(config.conjur_authn_login, 'admin')
    self.assertEqual(config.conjur_api_key, 'apikey')
    self.assertIsNone(config.bitbucket_pipe_shared_storage_dir)
  
  @patch.dict(os.environ, {
    'CONJUR_URL': 'https://conjur.example.com',
    'CONJUR_ACCOUNT': 'myaccount',
    'SECRETS': '',
    'CONJUR_AUTHN_LOGIN': 'host/myhost',
    'CONJUR_API_KEY': 'apikey'
  }, clear=True)
  def test_fetch_config_from_env_empty_secrets(self):
    config = PipeConfig.fetch_config_from_env()
    self.assertEqual(config.conjur_url, 'https://conjur.example.com')
    self.assertEqual(config.conjur_account, 'myaccount')
    self.assertEqual(config.secrets, [])
    self.assertEqual(config.conjur_authn_login, 'host/myhost')
    self.assertEqual(config.conjur_api_key, 'apikey')
    self.assertIsNone(config.bitbucket_pipe_shared_storage_dir)

if __name__ == '__main__':
  unittest.main()
