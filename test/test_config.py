import os
import unittest
from unittest.mock import patch

from pipe.pipe import PipeConfig


class TestConfig(unittest.TestCase):

    @patch.dict(os.environ, {
        'CONJUR_URL': 'https://conjur.example.com',
        'CONJUR_ACCOUNT': 'myaccount',
        'CONJUR_SERVICE_ID': 'bitbucket',
        'SECRETS': 'secret1,secret2',
        'BITBUCKET_PIPE_STORAGE_DIR': '/tmp',
        'BITBUCKET_STEP_OIDC_TOKEN': 'jwt-content'
    })
    def test_fetch_config_from_env(self):
        config = PipeConfig.fetch_config_from_env()
        self.assertIsInstance(config, PipeConfig)
        self.assertEqual(config.conjur_url, 'https://conjur.example.com')
        self.assertEqual(config.conjur_account, 'myaccount')
        self.assertEqual(config.secrets, ['secret1','secret2'])
        self.assertEqual(config.conjur_service_id, 'bitbucket')
        self.assertEqual(config.output_dir, '/tmp')
        self.assertEqual(config.jwt, 'jwt-content')

    @patch.dict(os.environ, {
        'CONJUR_URL': 'https://conjur.example.com',
        'SECRETS': 'single_secret',
        'BITBUCKET_STEP_OIDC_TOKEN': 'jwt-content'
    }, clear=True)
    def test_fetch_config_from_env_without_optional(self):
        config = PipeConfig.fetch_config_from_env()
        self.assertEqual(config.conjur_url, 'https://conjur.example.com')
        self.assertEqual(config.conjur_account, 'conjur')
        self.assertEqual(config.secrets, ['single_secret'])
        self.assertEqual(config.conjur_service_id, 'bitbucket')
        self.assertIsNone(config.output_dir)
        self.assertEqual(config.jwt, 'jwt-content')

    @patch.dict(os.environ, {
        'CONJUR_URL': 'https://conjur.example.com',
        'CONJUR_ACCOUNT': 'myaccount',
        'SECRETS': '',
        'CONJUR_SERVICE_ID': 'bitbucket',
        'BITBUCKET_STEP_OIDC_TOKEN': 'jwt-content'
    }, clear=True)
    def test_fetch_config_from_env_empty_secrets(self):
        config = PipeConfig.fetch_config_from_env()
        self.assertEqual(config.conjur_url, 'https://conjur.example.com')
        self.assertEqual(config.conjur_account, 'myaccount')
        self.assertEqual(config.secrets, [])
        self.assertEqual(config.conjur_service_id, 'bitbucket')
        self.assertIsNone(config.output_dir)
        self.assertEqual(config.jwt, 'jwt-content')

if __name__ == '__main__':
    unittest.main()
