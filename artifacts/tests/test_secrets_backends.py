import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from aho.secrets.backends.age import AgeBackend
from aho.secrets.backends.keyring_linux import LinuxKeyringStore

class TestSecretsBackends(unittest.TestCase):
    
    @patch('shutil.which')
    def test_age_available(self, mock_which):
        mock_which.return_value = "/usr/bin/age"
        backend = AgeBackend()
        self.assertTrue(backend.is_available())
        
        mock_which.return_value = None
        backend = AgeBackend()
        self.assertFalse(backend.is_available())

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_age_encrypt_decrypt(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/age"
        backend = AgeBackend()
        
        # Mock encrypt
        mock_run.return_value = MagicMock(stdout=b"encrypted_data", returncode=0)
        result = backend.encrypt("secret", "passphrase")
        self.assertEqual(result, b"encrypted_data")
        
        # Verify call args
        args, kwargs = mock_run.call_args
        self.assertIn("--passphrase", args[0])
        self.assertEqual(kwargs['input'], b"secret")
        self.assertEqual(kwargs['env']['AGE_PASSPHRASE'], "passphrase")
        
        # Mock decrypt
        mock_run.return_value = MagicMock(stdout=b"secret", returncode=0)
        result = backend.decrypt(b"encrypted_data", "passphrase")
        self.assertEqual(result, "secret")

    @patch('shutil.which')
    def test_keyring_available(self, mock_which):
        mock_which.return_value = "/usr/bin/keyctl"
        store = LinuxKeyringStore()
        self.assertTrue(store.is_available())
        
        mock_which.return_value = None
        store = LinuxKeyringStore()
        self.assertFalse(store.is_available())

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_keyring_store_retrieve(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/keyctl"
        store = LinuxKeyringStore()
        
        # Mock store
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(store.store("mypassphrase"))
        
        # Mock retrieve
        # First call to 'request'
        mock_request = MagicMock(stdout=b"12345\n", returncode=0)
        # Second call to 'pipe'
        mock_pipe = MagicMock(stdout=b"mypassphrase", returncode=0)
        mock_run.side_effect = [mock_request, mock_pipe]
        
        result = store.retrieve()
        self.assertEqual(result, "mypassphrase")

    @unittest.skipIf(not AgeBackend().is_available() or not sys.stdin.isatty(), "age binary not found or no TTY available")
    def test_age_integration(self):
        backend = AgeBackend()
        passphrase = "test-passphrase-integration"
        data = "hello world"
        
        encrypted = backend.encrypt(data, passphrase)
        self.assertIsInstance(encrypted, bytes)
        self.assertNotEqual(encrypted.decode(errors='ignore'), data)
        
        decrypted = backend.decrypt(encrypted, passphrase)
        self.assertEqual(decrypted, data)

    @unittest.skipIf(sys.platform != "linux" or not LinuxKeyringStore().is_available(), "keyctl not available")
    def test_keyring_integration(self):
        store = LinuxKeyringStore()
        passphrase = "test-passphrase-keyring"
        
        # Clear if exists
        store.clear()
        
        # Store
        self.assertTrue(store.store(passphrase))
        
        # Retrieve
        retrieved = store.retrieve()
        self.assertEqual(retrieved, passphrase)
        
        # Clear
        self.assertTrue(store.clear())
        self.assertIsNone(store.retrieve())

if __name__ == "__main__":
    unittest.main()
