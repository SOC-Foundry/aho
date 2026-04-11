import json
from pathlib import Path
from .backends.fernet import FernetBackend
from .session import get_passphrase

SECRETS_FILE = Path.home() / ".config" / "aho" / "secrets.fish.fernet"

def get_secrets_path() -> Path:
    return SECRETS_FILE

def _get_backend():
    return FernetBackend()

def _load_raw() -> bytes:
    if not SECRETS_FILE.exists():
        return b""
    return SECRETS_FILE.read_bytes()

def _save_raw(blob: bytes):
    SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SECRETS_FILE.write_bytes(blob)
    SECRETS_FILE.chmod(0o600)

def read_secrets() -> dict:
    """Read and decrypt all secrets from the store."""
    blob = _load_raw()
    if not blob:
        return {}
    
    passphrase = get_passphrase()
    if not passphrase:
        raise RuntimeError("Session locked. Run 'aho secret unlock' first.")
        
    plaintext = _get_backend().decrypt(blob, passphrase)
    try:
        data = json.loads(plaintext)
        # Ensure it's a nested dict
        if not isinstance(data, dict):
            return {}
        return data
    except json.JSONDecodeError:
        return {}

def write_secrets(secrets: dict):
    """Encrypt and write all secrets to the store."""
    passphrase = get_passphrase()
    if not passphrase:
        raise RuntimeError("Session locked. Run 'aho secret unlock' first.")
        
    plaintext = json.dumps(secrets, indent=2)
    blob = _get_backend().encrypt(plaintext, passphrase)
    _save_raw(blob)

def add_secret(project: str, name: str, value: str):
    """Add or update a secret in the store."""
    secrets = read_secrets()
    if project not in secrets:
        secrets[project] = {}
    secrets[project][name] = value
    write_secrets(secrets)

def get_secret(project: str, name: str) -> str:
    """Retrieve a secret from the store."""
    secrets = read_secrets()
    return secrets.get(project, {}).get(name)

def remove_secret(project: str, name: str):
    """Remove a secret from the store."""
    secrets = read_secrets()
    if project in secrets and name in secrets[project]:
        del secrets[project][name]
        if not secrets[project]:
            del secrets[project]
        write_secrets(secrets)

def list_secret_names(project: str = None) -> list:
    """List all secret names in the store, optionally filtered by project."""
    try:
        secrets = read_secrets()
        if project:
            return list(secrets.get(project, {}).keys())
        
        # Flatten for legacy compatibility or full list
        names = []
        for p, keys in secrets.items():
            for k in keys:
                names.append(f"{p}:{k}")
        return names
    except RuntimeError:
        raise

def init_secrets_file(passphrase: str):
    """Initialize a new secrets file with the given passphrase."""
    from .session import unlock
    unlock(passphrase)
    write_secrets({})
