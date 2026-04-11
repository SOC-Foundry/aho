import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os
from aho.install import migrate_config_fish

class TestMigrateConfigFish(unittest.TestCase):
    
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.tmp_dir.name) / "config.fish"
        self.config_content = (
            "# Existing config\n"
            "set -gx KJTCOM_API_KEY \"secret123\"\n"
            "set -x OTHER_TOKEN \"token456\"\n"
            "set -gx REGULAR_VAR \"value\"\n"
            "# >>> iao-middleware >>>\n"
            "old iao stuff\n"
            "# <<< iao-middleware <<<\n"
        )
        self.config_path.write_text(self.config_content)

    def tearDown(self):
        self.tmp_dir.cleanup()

    @patch('builtins.input')
    @patch('getpass.getpass')
    @patch('aho.secrets.session.is_unlocked')
    @patch('aho.secrets.session.unlock')
    @patch('aho.secrets.store.add_secret')
    @patch('aho.secrets.store.write_secrets')
    @patch('subprocess.run')
    def test_migrate(self, mock_run, mock_write_secrets, mock_add_secret, 
                     mock_unlock, mock_is_unlocked, mock_getpass, mock_input):
        
        mock_input.side_effect = ['y', 'y']  # Confirm both secrets
        mock_is_unlocked.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        migrate_config_fish.migrate(config_path=self.config_path)
        
        # Verify add_secret calls
        self.assertEqual(mock_add_secret.call_count, 2)
        mock_add_secret.assert_any_call("KJTCOM_API_KEY", "secret123")
        mock_add_secret.assert_any_call("OTHER_TOKEN", "token456")
        
        # Verify config.fish content
        new_content = self.config_path.read_text()
        self.assertNotIn("KJTCOM_API_KEY", new_content)
        self.assertNotIn("OTHER_TOKEN", new_content)
        self.assertIn("REGULAR_VAR", new_content)
        self.assertIn("# >>> aho >>>", new_content)
        self.assertNotIn("iao-middleware", new_content)
        
        # Verify backup exists
        backups = list(Path(self.tmp_dir.name).glob("config.fish.aho-migrate-backup-*"))
        self.assertEqual(len(backups), 1)

if __name__ == "__main__":
    unittest.main()
