import sys
import getpass
from pathlib import Path
from . import session
from . import store

def cmd_list(args):
    try:
        # Check if project was optionally provided (though not in parser yet for list)
        project = getattr(args, "project", None)
        names = store.list_secret_names(project)
        if not names:
            print("(no secrets stored)")
        else:
            for name in sorted(names):
                print(name)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

def cmd_get(args):
    try:
        value = store.get_secret(args.project, args.name)
        if value is None:
            print(f"ERROR: secret '{args.project}:{args.name}' not found")
            sys.exit(1)
        
        if args.raw:
            sys.stdout.write(value)
        else:
            print(f"{args.project}:{args.name}={value}")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

def cmd_set(args):
    try:
        value = args.value
        if not value:
            value = getpass.getpass(f"Enter value for {args.project}:{args.name}: ")
        
        store.add_secret(args.project, args.name, value)
        print(f"Stored secret: {args.project}:{args.name}")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

def cmd_rm(args):
    try:
        store.remove_secret(args.project, args.name)
        print(f"Removed secret: {args.project}:{args.name}")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

def cmd_unlock(args):
    if session.is_unlocked():
        print("Session already unlocked.")
        return
        
    passphrase = getpass.getpass("Enter aho master passphrase: ")
    if session.unlock(passphrase):
        print("Session unlocked.")
    else:
        print("ERROR: failed to unlock session (keyring error)")
        sys.exit(1)

def cmd_lock(args):
    if session.lock():
        print("Session locked.")
    else:
        print("ERROR: failed to lock session")
        sys.exit(1)

def cmd_status(args):
    unlocked = session.is_unlocked()
    status = "unlocked" if unlocked else "locked"
    print(f"Status: {status}")
    if unlocked:
        try:
            count = len(store.list_secret_names())
            print(f"Secrets: {count}")
        except Exception:
            pass

def cmd_rotate(args):
    try:
        value = store.get_secret(args.project, args.name)
        if value is None:
            print(f"ERROR: secret '{args.project}:{args.name}' not found")
            sys.exit(1)
            
        print(f"Rotating secret: {args.project}:{args.name}")
        print(f"Current value: {value}")
        
        new_value = getpass.getpass("Enter new value: ")
        if not new_value:
            print("Rotation cancelled (empty value).")
            return
            
        store.add_secret(args.project, args.name, new_value)
        print("Secret rotated successfully.")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

def cmd_export(args):
    if args.fish:
        try:
            secrets = store.read_secrets()
            for project, keys in secrets.items():
                for name, value in keys.items():
                    # Export with project prefix
                    env_name = f"{project.upper()}_{name}"
                    print(f"set -gx {env_name} \"{value}\"")
        except RuntimeError as e:
            print(f"ERROR: {e}")
            sys.exit(1)
    else:
        print(str(store.get_secrets_path()))

def cmd_import(args):
    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        sys.exit(1)
        
    target = store.get_secrets_path()
    import shutil
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, target)
    print(f"Imported secrets from {path}")
