import sys
from typing import Optional
from .backends.keyring_linux import LinuxKeyringStore

def get_session_store():
    """Get the appropriate passphrase store for the current platform."""
    if sys.platform == "linux":
        return LinuxKeyringStore()
    # Future: macOS and Windows stores
    return None

def unlock(passphrase: str) -> bool:
    """Unlock the session by storing the passphrase in the keyring."""
    store = get_session_store()
    if store and store.is_available():
        return store.store(passphrase)
    return False

def lock() -> bool:
    """Lock the session by clearing the passphrase from the keyring."""
    store = get_session_store()
    if store and store.is_available():
        return store.clear()
    return False

def is_unlocked() -> bool:
    """Check if the session is currently unlocked."""
    store = get_session_store()
    if store and store.is_available():
        return store.retrieve() is not None
    return False

def get_passphrase() -> Optional[str]:
    """Retrieve the session passphrase from the keyring."""
    store = get_session_store()
    if store and store.is_available():
        return store.retrieve()
    return None
