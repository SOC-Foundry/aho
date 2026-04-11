import subprocess
import shutil
from typing import Optional
from .base import PassphraseStore

class LinuxKeyringStore(PassphraseStore):
    """Passphrase store using the Linux kernel keyring (keyctl)."""
    
    KEY_TYPE = "user"
    KEY_DESCRIPTION = "iao_passphrase"
    KEYRING = "@s"  # Session keyring

    def is_available(self) -> bool:
        """Check if 'keyctl' binary is available."""
        return shutil.which("keyctl") is not None

    def store(self, passphrase: str) -> bool:
        """Store the passphrase in the session keyring."""
        if not self.is_available():
            return False
            
        try:
            # keyctl padd user iao_passphrase @s
            # Passphrase is read from stdin
            subprocess.run(
                ["keyctl", "padd", self.KEY_TYPE, self.KEY_DESCRIPTION, self.KEYRING],
                input=passphrase.encode(),
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def retrieve(self) -> Optional[str]:
        """Retrieve the passphrase from the session keyring."""
        if not self.is_available():
            return None
            
        try:
            # keyctl request user iao_passphrase
            # This gets the key ID
            process = subprocess.run(
                ["keyctl", "request", self.KEY_TYPE, self.KEY_DESCRIPTION],
                capture_output=True,
                check=True
            )
            key_id = process.stdout.decode().strip()
            
            # keyctl pipe <key_id>
            # This prints the value
            process = subprocess.run(
                ["keyctl", "pipe", key_id],
                capture_output=True,
                check=True
            )
            return process.stdout.decode()
        except subprocess.CalledProcessError:
            return None

    def clear(self) -> bool:
        """Clear the passphrase from the session keyring."""
        if not self.is_available():
            return False
            
        try:
            # keyctl request user iao_passphrase
            process = subprocess.run(
                ["keyctl", "request", self.KEY_TYPE, self.KEY_DESCRIPTION],
                capture_output=True,
                check=True
            )
            key_id = process.stdout.decode().strip()
            
            # keyctl unlink <key_id> @s
            subprocess.run(
                ["keyctl", "unlink", key_id, self.KEYRING],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            # If it doesn't exist, clearing is technically successful or already done
            return True
