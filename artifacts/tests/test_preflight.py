import unittest
from unittest.mock import patch, MagicMock
from aho.preflight import checks

class TestPreflight(unittest.TestCase):
    
    @patch('sys.version_info')
    def test_check_python_version(self, mock_v):
        mock_v.major = 3
        mock_v.minor = 14
        mock_v.micro = 3
        ok, msg = checks.check_python_version()
        self.assertTrue(ok)
        self.assertIn("3.14.3", msg)
        
        mock_v.minor = 9
        ok, msg = checks.check_python_version()
        self.assertFalse(ok)

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_pip(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/pip"
        mock_run.return_value = MagicMock(stdout="pip 23.0", returncode=0)
        ok, msg = checks.check_pip()
        self.assertTrue(ok)
        
        mock_which.return_value = None
        ok, msg = checks.check_pip()
        self.assertFalse(ok)

    @patch('shutil.disk_usage')
    def test_check_disk_space(self, mock_usage):
        # 10GB free
        mock_usage.return_value = (100*2**30, 90*2**30, 10*2**30)
        ok, msg = checks.check_disk_space()
        self.assertTrue(ok)
        self.assertIn("10 GB free", msg)
        
        # 2GB free
        mock_usage.return_value = (100*2**30, 98*2**30, 2*2**30)
        ok, msg = checks.check_disk_space()
        self.assertFalse(ok)

if __name__ == "__main__":
    unittest.main()
