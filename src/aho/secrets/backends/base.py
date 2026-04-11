from abc import ABC, abstractmethod
from typing import Optional

class SecretBackend(ABC):
    """Abstract base class for secrets encryption backends."""
    
    @abstractmethod
    def encrypt(self, data: str, passphrase: str) -> bytes:
        """Encrypt data with a passphrase."""
        pass

    @abstractmethod
    def decrypt(self, blob: bytes, passphrase: str) -> str:
        """Decrypt data with a passphrase."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend and its dependencies are available on the current platform."""
        pass

class PassphraseStore(ABC):
    """Abstract base class for session-based passphrase storage."""

    @abstractmethod
    def store(self, passphrase: str) -> bool:
        """Store the passphrase in the session-level store."""
        pass

    @abstractmethod
    def retrieve(self) -> Optional[str]:
        """Retrieve the passphrase from the session-level store."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear the passphrase from the session-level store."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the store and its dependencies are available on the current platform."""
        pass
