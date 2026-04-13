"""Tests for Nemotron classifier — W2 0.2.13.

Three test cases:
1. Verified-good: well-formed classification → returns real category
2. Verified-bad (malformed): unparseable response → raises NemotronParseError
3. Verified-bad (connection): Ollama unreachable → raises NemotronConnectionError
"""
from unittest.mock import MagicMock, patch

import pytest
import requests


@patch("aho.artifacts.nemotron_client.log_event")
@patch("aho.artifacts.nemotron_client.requests.post")
def test_good_classification_returns_real_category(mock_post, mock_log):
    """Well-formed Nemotron response returns the matched category, not categories[-1]."""
    from aho.artifacts.nemotron_client import classify

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"response": "code_runner"}
    mock_post.return_value = mock_resp

    categories = ["assistant", "code_runner", "reviewer"]
    result = classify("write a python script to sort a list", categories)

    # Must return the actual matched category, NOT categories[-1] ("reviewer")
    assert result == "code_runner"
    assert result != categories[-1]


@patch("aho.artifacts.nemotron_client.log_event")
@patch("aho.artifacts.nemotron_client.requests.post")
def test_unparseable_response_raises_nemotron_parse_error(mock_post, mock_log):
    """Nemotron response that matches no category raises NemotronParseError."""
    from aho.artifacts.nemotron_client import classify, NemotronParseError

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "response": "I'm not sure what category this belongs to, it could be anything really"
    }
    mock_post.return_value = mock_resp

    categories = ["assistant", "code_runner", "reviewer"]
    with pytest.raises(NemotronParseError) as exc_info:
        classify("some ambiguous task", categories)

    assert exc_info.value.raw_response != ""
    assert "does not match any category" in str(exc_info.value)


@patch("aho.artifacts.nemotron_client.log_event")
@patch("aho.artifacts.nemotron_client.requests.post")
def test_connection_error_raises_nemotron_connection_error(mock_post, mock_log):
    """Ollama unreachable raises NemotronConnectionError, not silent fallback."""
    from aho.artifacts.nemotron_client import classify, NemotronConnectionError

    mock_post.side_effect = requests.ConnectionError("Connection refused")

    categories = ["assistant", "code_runner", "reviewer"]
    with pytest.raises(NemotronConnectionError) as exc_info:
        classify("any task", categories)

    assert exc_info.value.original_error is not None
    assert "localhost:11434" in str(exc_info.value)
