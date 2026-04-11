import unittest
from unittest.mock import patch, MagicMock
from aho.secrets import cli as secrets_cli

class TestSecretsCLI(unittest.TestCase):
    
    @patch('aho.secrets.store.list_secret_names')
    def test_cmd_list(self, mock_list):
        mock_list.return_value = ["API_KEY", "DB_PASSWORD"]
        args = MagicMock()
        
        with patch('sys.stdout') as mock_stdout:
            secrets_cli.cmd_list(args)
            output = "".join(call.args[0] for call in mock_stdout.write.call_args_list)
            self.assertIn("API_KEY", output)
            self.assertIn("DB_PASSWORD", output)

    @patch('aho.secrets.store.read_secrets')
    def test_cmd_get(self, mock_read):
        mock_read.return_value = {"ahomw": {"API_KEY": "secret123"}}
        args = MagicMock()
        args.project = "ahomw"
        args.name = "API_KEY"
        args.raw = False
        
        with patch('aho.secrets.store.get_secret') as mock_get:
            mock_get.return_value = "secret123"
            with patch('sys.stdout') as mock_stdout:
                secrets_cli.cmd_get(args)
                output = "".join(call.args[0] for call in mock_stdout.write.call_args_list)
                self.assertIn("ahomw:API_KEY=secret123", output)

    @patch('aho.secrets.store.add_secret')
    def test_cmd_set(self, mock_add):
        args = MagicMock()
        args.project = "ahomw"
        args.name = "API_KEY"
        args.value = "secret123"
        secrets_cli.cmd_set(args)
        mock_add.assert_called_with("ahomw", "API_KEY", "secret123")

    @patch('aho.secrets.session.is_unlocked')
    @patch('getpass.getpass')
    @patch('aho.secrets.session.unlock')
    def test_cmd_unlock(self, mock_unlock, mock_getpass, mock_is_unlocked):
        mock_is_unlocked.return_value = False
        mock_getpass.return_value = "mypassphrase"
        mock_unlock.return_value = True
        args = MagicMock()
        
        secrets_cli.cmd_unlock(args)
        mock_unlock.assert_called_with("mypassphrase")

    @patch('aho.secrets.session.lock')
    def test_cmd_lock(self, mock_lock):
        mock_lock.return_value = True
        args = MagicMock()
        secrets_cli.cmd_lock(args)
        mock_lock.assert_called_once()

if __name__ == "__main__":
    unittest.main()
