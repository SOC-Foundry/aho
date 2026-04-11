"""Telegram notification logic for aho."""
import os
import requests
from aho.secrets import session as secrets_session


def _get_creds(project_code: str):
    """Retrieve Telegram credentials from aho secrets with env fallback."""
    token = None
    chat_id = None
    
    try:
        from aho.secrets import store as secrets_store
        token = secrets_store.get_secret(project_code, "TELEGRAM_BOT_TOKEN")
        chat_id = secrets_store.get_secret(project_code, "TELEGRAM_CHAT_ID")
    except Exception:
        # Ignore errors from secret store (e.g. locked, age missing)
        pass
        
    if not token or not chat_id:
        # Fallback to legacy env names or project-prefixed envs
        token = os.environ.get(f"{project_code.upper()}_TELEGRAM_BOT_TOKEN") or \
                os.environ.get("KJTCOM_TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get(f"{project_code.upper()}_TELEGRAM_CHAT_ID") or \
                  os.environ.get("KJTCOM_TELEGRAM_CHAT_ID")
                  
    return token, chat_id


def send_message(project_code: str, text: str) -> bool:
    """Send a plain text message to a Telegram chat."""
    token, chat_id = _get_creds(project_code)
    if not token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception:
        return False


def send_iteration_complete(project_code: str, iteration: str, bundle_path: str, run_path: str) -> bool:
    """Send a structured iteration-complete notification."""
    text = (
        f"✅ Iteration {iteration} COMPLETE\n"
        f"Project: {project_code}\n\n"
        f"Bundle: {bundle_path}\n"
        f"Report: {run_path}\n\n"
        f"Status: Review Pending"
    )
    return send_message(project_code, text)
