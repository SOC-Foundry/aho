#!/usr/bin/env python3
"""Firestore query execution for dual retrieval path. Generalized from kjtcom."""
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

from aho.paths import find_project_root
from aho.logger import log_event

# Configuration
try:
    PROJECT_ROOT = find_project_root()
    PROJECT_NAME = os.environ.get("AHO_PROJECT_NAME", os.environ.get("IAO_PROJECT_NAME", PROJECT_ROOT.name)
except Exception:
    PROJECT_ROOT = Path.cwd()
    PROJECT_NAME = "unknown"

# Firebase Admin SDK - lazy init
_db = None


def _get_db():
    """Initialize Firebase Admin SDK and return Firestore client."""
    global _db
    if _db is not None:
        return _db

    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        # Use project-specific SA key from global gcloud config
        sa_path = os.path.expanduser(f"~/.config/gcloud/{PROJECT_NAME}-sa.json")
        if not os.path.exists(sa_path):
            # Fallback for tripledb if named differently
            if PROJECT_NAME == "tripledb":
                sa_path = os.path.expanduser("~/.config/gcloud/tripledb-e0f77-sa.json")
            
        if not os.path.exists(sa_path):
            raise RuntimeError(f"Service account key not found at {sa_path}")
            
        cred = credentials.Certificate(sa_path)
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db


def execute_query(filters: Dict[str, Any], intent: str, sort_field: str = None, 
                  sort_order: str = "desc", limit: int = None,
                  return_docs: bool = False) -> Union[str, Tuple[str, List[Dict[str, Any]]]]:
    """Execute a Firestore query with filters and return formatted results."""
    start = time.time()
    agent = os.environ.get("AHO_AGENT", os.environ.get("IAO_AGENT", "aho-cli"))
    
    try:
        db = _get_db()
        from google.cloud.firestore_v1.base_query import FieldFilter

        # Collection name: should this be generalized? 
        # kjtcom used "locations". aho projects might use different ones.
        # We'll use "locations" as default but allow override.
        collection_name = os.environ.get("IAO_FIRESTORE_COLLECTION", "locations")
        query = db.collection(collection_name)
        array_filters = []

        for field, value in filters.items():
            if isinstance(value, list):
                # Only one array-contains per query allowed by Firestore
                if not array_filters:
                    query = query.where(filter=FieldFilter(field, "array_contains", value[0]))
                array_filters.append((field, value))
            else:
                query = query.where(filter=FieldFilter(field, "==", value))

        # Fetch and post-filter
        results = query.stream()
        docs = [doc.to_dict() for doc in results]
        
        # Post-filter for additional array values
        for field, value in array_filters:
            for extra_val in value[1:]:
                docs = [d for d in docs if extra_val in d.get(field, [])]
        # Post-filter for array fields that weren't the primary array-contains
        for field, value in array_filters[1:]:
            docs = [d for d in docs if value[0] in d.get(field, [])]

        # Client-side sort
        if sort_field:
            def _get_nested(doc, path):
                parts = path.split('.')
                val = doc
                for p in parts:
                    if isinstance(val, dict):
                        val = val.get(p)
                    else:
                        return None
                return val

            docs.sort(key=lambda d: _get_nested(d, sort_field) or 0,
                      reverse=(sort_order == "desc"))
            if limit and isinstance(limit, int):
                docs = docs[:limit]

        total = len(docs)
        latency = int((time.time() - start) * 1000)

        log_event("api_call", agent, "firestore", "query",
                  input_summary=f"filters={filters}, intent={intent}, sort={sort_field}, limit={limit}"[:200],
                  output_summary=f"{total} docs returned",
                  latency_ms=latency, status="success")

        if intent == "count":
            text = format_entity_count(docs, filters)
        elif intent == "list":
            text = format_entity_list(docs, limit=20)
        else:
            text = format_entity_detail(docs, limit=10)

        if return_docs:
            return text, docs
        return text

    except Exception as e:
        latency = int((time.time() - start) * 1000)
        log_event("api_call", agent, "firestore", "query",
                  input_summary=f"filters={filters}"[:200],
                  status="error", error=str(e), latency_ms=latency)
        error_text = f"Firestore query error: {e}"
        if return_docs:
            return error_text, []
        return error_text


def format_entity_count(docs: List[Dict[str, Any]], filters: Dict[str, Any] = None) -> str:
    """Format count response."""
    total = len(docs)
    if total == 0:
        return "0 results found. Try broadening your search."
    return f"{total} results found."


def format_entity_list(docs: List[Dict[str, Any]], limit: int = 20) -> str:
    """Format list of entities."""
    total = len(docs)
    if total == 0:
        return "0 results found. Try broadening your search."

    lines = []
    for doc in docs[:limit]:
        name = _get_name(doc)
        city = _get_first(doc, 't_any_cities')
        state = _get_first(doc, 't_any_states')
        location = ", ".join(filter(None, [city, state]))
        line = f"- {name}"
        if location:
            line += f" ({location})"
        lines.append(line)

    result = "\n".join(lines)
    if total > limit:
        result += f"\n\n...and {total - limit} more ({total} total)"
    else:
        result += f"\n\n{total} results."
    return result


def format_entity_detail(docs: List[Dict[str, Any]], limit: int = 10) -> str:
    """Format detailed entity info."""
    total = len(docs)
    if total == 0:
        return "0 results found. Try broadening your search."

    lines = []
    for doc in docs[:limit]:
        name = _get_name(doc)
        parts = [f"**{name}**"]
        for key in ['t_any_cities', 't_any_states', 't_any_countries',
                     't_any_cuisines', 't_any_categories']:
            val = doc.get(key, [])
            if val:
                label = key.replace('t_any_', '')
                parts.append(f"  {label}: {', '.join(val[:5])}")
        lines.append("\n".join(parts))

    result = "\n\n".join(lines)
    if total > limit:
        result += f"\n\n...and {total - limit} more ({total} total)"
    return result


def _get_name(doc: Dict[str, Any]) -> str:
    """Get display name from doc."""
    names = doc.get('t_any_names', [])
    if names:
        return names[0]
    return doc.get('t_name', 'Unknown')


def _get_first(doc: Dict[str, Any], field: str) -> str:
    """Get first value from an array field."""
    val = doc.get(field, [])
    return val[0] if val else ''


if __name__ == '__main__':
    # Standalone test
    test_filters = {'t_log_type': 'tripledb'}
    test_intent = 'count'
    print(execute_query(test_filters, test_intent))
