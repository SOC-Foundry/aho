import subprocess
import shutil
import os
from typing import Optional
from .base import SecretBackend

class AgeBackend(SecretBackend):
    """Secret backend using the 'age' encryption tool."""
    
    def __init__(self, binary_path: Optional[str] = None):
        self.binary_path = binary_path or shutil.which("age")

    def is_available(self) -> bool:
        """Check if 'age' binary is available."""
        return self.binary_path is not None

    def encrypt(self, data: str, passphrase: str) -> bytes:
        """Encrypt data with a passphrase using 'age'."""
        if not self.is_available():
            raise RuntimeError("age binary not found. Please install it first.")
            
        env = os.environ.copy()
        env["AGE_PASSPHRASE"] = passphrase
        
        # Use '-' for stdin, --passphrase/-p for passphrase encryption
        cmd = [self.binary_path, "--passphrase", "--output", "-", "-"]
        
        try:
            process = subprocess.run(
                cmd,
                input=data.encode(),
                env=env,
                capture_output=True,
                check=True
            )
            return process.stdout
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode()
            raise RuntimeError(f"age encryption failed: {error_msg}")

    def decrypt(self, blob: bytes, passphrase: str) -> str:
        """Decrypt data with a passphrase using 'age'."""
        if not self.is_available():
            raise RuntimeError("age binary not found. Please install it first.")
            
        env = os.environ.copy()
        env["AGE_PASSPHRASE"] = passphrase
        
        # age --decrypt/-d
        cmd = [self.binary_path, "--decrypt", "--output", "-", "-"]
        
        try:
            process = subprocess.run(
                cmd,
                input=blob,
                env=env,
                capture_output=True,
                check=True
            )
            return process.stdout.decode()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode()
            raise RuntimeError(f"age decryption failed: {error_msg}")
