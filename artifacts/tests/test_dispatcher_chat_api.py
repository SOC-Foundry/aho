"""Unit tests for dispatcher /api/chat migration (0.2.14 W1.5 D2).

Verifies:
- /api/chat endpoint used (not /api/generate)
- Request payload contains messages array (not prompt string)
- num_ctx present in request options
- stop tokens present in request options
- Response extraction reads from .message.content (chat API shape)
- System prompt omission produces user-only messages array
"""
import json
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

from aho.pipeline.dispatcher import dispatch, DEFAULT_NUM_CTX, STOP_TOKENS


def _make_mock_response(content: str, model: str = "qwen3.5:9b"):
    """Build a mock HTTP response matching Ollama /api/chat shape."""
    body = {
        "model": model,
        "message": {"role": "assistant", "content": content},
        "total_duration": 5_000_000_000,  # 5s in nanoseconds
        "done": True,
    }
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestDispatcherChatAPI(unittest.TestCase):

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_uses_chat_endpoint(self, mock_urlopen):
        """Dispatcher must call /api/chat, not /api/generate."""
        mock_urlopen.return_value = _make_mock_response("ok")
        dispatch("qwen3.5:9b", "test prompt", system="test system")
        req = mock_urlopen.call_args[0][0]
        self.assertIn("/api/chat", req.full_url)
        self.assertNotIn("/api/generate", req.full_url)

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_payload_has_messages_array(self, mock_urlopen):
        """Payload must contain messages array, not prompt string."""
        mock_urlopen.return_value = _make_mock_response("ok")
        dispatch("qwen3.5:9b", "user input", system="system instruction")
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data)
        self.assertIn("messages", payload)
        self.assertNotIn("prompt", payload)
        self.assertIsInstance(payload["messages"], list)
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][0]["content"], "system instruction")
        self.assertEqual(payload["messages"][1]["role"], "user")
        self.assertEqual(payload["messages"][1]["content"], "user input")

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_num_ctx_in_options(self, mock_urlopen):
        """Request options must include num_ctx."""
        mock_urlopen.return_value = _make_mock_response("ok")
        dispatch("qwen3.5:9b", "test")
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data)
        self.assertIn("options", payload)
        self.assertEqual(payload["options"]["num_ctx"], DEFAULT_NUM_CTX)

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_stop_tokens_in_options(self, mock_urlopen):
        """Request options must include stop tokens for Qwen template."""
        mock_urlopen.return_value = _make_mock_response("ok")
        dispatch("qwen3.5:9b", "test")
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data)
        self.assertIn("options", payload)
        self.assertEqual(payload["options"]["stop"], STOP_TOKENS)
        self.assertIn("<|endoftext|>", payload["options"]["stop"])
        self.assertIn("<|im_end|>", payload["options"]["stop"])

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_response_from_message_content(self, mock_urlopen):
        """Response must be extracted from body.message.content (chat shape)."""
        mock_urlopen.return_value = _make_mock_response("the actual response")
        result = dispatch("qwen3.5:9b", "test")
        self.assertEqual(result["response"], "the actual response")
        self.assertIsNone(result["error"])

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_no_system_produces_user_only_messages(self, mock_urlopen):
        """When system=None, messages array has only the user message."""
        mock_urlopen.return_value = _make_mock_response("ok")
        dispatch("qwen3.5:9b", "user only")
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data)
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertEqual(payload["messages"][0]["content"], "user only")


if __name__ == "__main__":
    unittest.main()
