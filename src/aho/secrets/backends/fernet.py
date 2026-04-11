import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .base import SecretBackend

class FernetBackend(SecretBackend):
    """Secret backend using Python cryptography Fernet (AES-128)."""
    
    def __init__(self):
        # Fixed salt for local dev; enough for iteration scope.
        self.salt = b'aho-salt-0.1.4'

    def is_available(self) -> bool:
        return True

    def _derive_key(self, passphrase: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
        return key

    def encrypt(self, data: str, passphrase: str) -> bytes:
        key = self._derive_key(passphrase)
        f = Fernet(key)
        return f.encrypt(data.encode())

    def decrypt(self, blob: bytes, passphrase: str) -> str:
        key = self._derive_key(passphrase)
        f = Fernet(key)
        return f.decrypt(blob).decode()
