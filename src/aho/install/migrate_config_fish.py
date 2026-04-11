import os
import shutil
import datetime
import getpass
import subprocess
from pathlib import Path
from .secret_patterns import PATTERNS
from ..secrets import store, session

def migrate(dry_run: bool = False, config_path: Path = None):
    if config_path is None:
        config_path = Path.home() / ".config" / "fish" / "config.fish"
    
    if not config_path.exists():
        print(f"Fish config not found at {config_path}. Skipping migration.")
        return

    print(f"Scanning {config_path} for plaintext secrets...")
    content = config_path.read_text()
    lines = content.splitlines()
    
    migrated_secrets = {}
    remaining_lines = []
    
    for line in lines:
        matched = False
        for pattern in PATTERNS:
            match = pattern.search(line)
            if match:
                name, value = match.groups()
                confirm = input(f"Found {name}. Migrate to encrypted secrets? [Y/n] ")
                if confirm.lower() != 'n':
                    migrated_secrets[name] = value
                    matched = True
                    break
        
        if not matched:
            remaining_lines.append(line)

    if not migrated_secrets:
        print("No secrets identified for migration.")
        return

    if dry_run:
        print(f"Dry run: would migrate {len(migrated_secrets)} secrets.")
        for name in migrated_secrets:
            print(f"  - {name}")
        return

    # Backup
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = config_path.with_name(f"config.fish.aho-migrate-backup-{timestamp}")
    shutil.copy(config_path, backup_path)
    print(f"Backup created at {backup_path}")

    # Prompt for master passphrase if not unlocked
    if not session.is_unlocked():
        while True:
            passphrase = getpass.getpass("Enter new aho master passphrase for encryption: ")
            confirm = getpass.getpass("Confirm passphrase: ")
            if passphrase == confirm:
                session.unlock(passphrase)
                # Initialize store if it doesn't exist
                if not store.get_secrets_path().exists():
                    store.write_secrets({})
                break
            print("Passphrases do not match. Try again.")

    # Add secrets to store
    for name, value in migrated_secrets.items():
        store.add_secret(name, value)
    
    # Update config.fish
    # Replace the old iao-middleware block if present, or add at the end
    new_content = "\n".join(remaining_lines)
    
    # Check for existing iao-middleware block
    if "# >>> iao-middleware >>>" in new_content:
        # We should probably replace it
        import re
        new_content = re.sub(
            r'# >>> iao-middleware >>>.*?# <<< iao-middleware <<<', 
            '', 
            new_content, 
            flags=re.DOTALL
        )
    
    # Add new aho block
    iao_block = (
        "\n# >>> aho >>>\n"
        "if aho secret status | grep -q locked\n"
        "    aho secret unlock\n"
        "end\n"
        "aho secret export --fish | source\n"
        "set -gx IAO_HOME $HOME/dev/projects/aho\n"
        "# <<< aho <<<\n"
    )
    
    if "# <<< aho <<<" not in new_content:
        new_content = new_content.strip() + "\n" + iao_block
    
    config_path.write_text(new_content)
    print("Fish config updated successfully.")
    
    # Final syntax check
    try:
        subprocess.run(["fish", "--no-execute", str(config_path)], check=True)
        print("Fish config syntax check: OK")
    except Exception:
        print("WARNING: Fish config may have syntax errors. Please check manually.")
