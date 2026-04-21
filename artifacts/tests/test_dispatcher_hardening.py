"""Unit tests for dispatcher multi-model hardening (0.2.15 W2).

Covers:
- Per-model-family stop token dispatch
- GLM template prefix stripping
- Template leak detection
- Error type specificity (G083: no blanket except Exception)
- Retry with exponential backoff (transient only)
- No retry on template leak or model-not-found (systemic/permanent)
- Parameter validation (R7: num_ctx bounds)
- Model family resolution
- Model management helpers (unload, list, ensure_ready)
- Backward compatibility (STOP_TOKENS constant)
"""
import json
import time
import unittest
from unittest.mock import patch, MagicMock, call

from aho.pipeline.dispatcher import (
    dispatch,
    resolve_family,
    get_family_config,
    MODEL_FAMILY_CONFIG,
    STOP_TOKENS,
    DEFAULT_NUM_CTX,
    MIN_NUM_CTX,
    MAX_NUM_CTX,
    DispatchError,
    MalformedResponseError,
    TemplateLeakError,
    ModelUnavailableError,
    DispatchTimeoutError,
    _postprocess_response,
    _check_template_leak,
    _validate_num_ctx,
    unload_model,
    list_loaded_models,
)


def _chat_response(content: str, model: str = "qwen3.5:9b"):
    """Build a mock HTTP response matching Ollama /api/chat shape."""
    body = {
        "model": model,
        "message": {"role": "assistant", "content": content},
        "total_duration": 5_000_000_000,
        "done": True,
    }
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestModelFamilyResolution(unittest.TestCase):

    def test_qwen_family(self):
        self.assertEqual(resolve_family("qwen3.5:9b"), "qwen")

    def test_llama3_family(self):
        self.assertEqual(resolve_family("llama3.2:3b"), "llama3")

    def test_llama3_plain(self):
        self.assertEqual(resolve_family("llama3:8b"), "llama3")

    def test_glm_haervwe_prefix(self):
        self.assertEqual(resolve_family("haervwe/GLM-4.6V-Flash-9B:latest"), "glm")

    def test_glm_short(self):
        self.assertEqual(resolve_family("glm-4:9b"), "glm")

    def test_nemotron_family(self):
        self.assertEqual(resolve_family("nemotron-mini:4b"), "nemotron")

    def test_unknown_model(self):
        self.assertEqual(resolve_family("totally-unknown:7b"), "unknown")

    def test_case_insensitive(self):
        self.assertEqual(resolve_family("Qwen3.5:9B"), "qwen")
        self.assertEqual(resolve_family("LLAMA3.2:3B"), "llama3")


class TestFamilyStopTokens(unittest.TestCase):

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_qwen_gets_qwen_stops(self, mock_urlopen):
        mock_urlopen.return_value = _chat_response("ok", "qwen3.5:9b")
        dispatch("qwen3.5:9b", "test")
        payload = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(payload["options"]["stop"], ["<|endoftext|>", "<|im_end|>"])

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_llama_gets_llama_stops(self, mock_urlopen):
        mock_urlopen.return_value = _chat_response("ok", "llama3.2:3b")
        dispatch("llama3.2:3b", "test")
        payload = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(payload["options"]["stop"], ["<|eot_id|>", "<|end_of_text|>"])

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_glm_gets_glm_stops(self, mock_urlopen):
        mock_urlopen.return_value = _chat_response("ok", "haervwe/GLM-4.6V-Flash-9B:latest")
        dispatch("haervwe/GLM-4.6V-Flash-9B:latest", "test")
        payload = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(payload["options"]["stop"], ["<|endoftext|>", "<|end_of_box|>"])

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_nemotron_gets_chatml_stops(self, mock_urlopen):
        mock_urlopen.return_value = _chat_response("ok", "nemotron-mini:4b")
        dispatch("nemotron-mini:4b", "test")
        payload = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(payload["options"]["stop"], ["<|endoftext|>", "<|im_end|>"])


class TestGLMConfig(unittest.TestCase):

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_glm_num_gpu_30(self, mock_urlopen):
        """GLM must use num_gpu=30 (partial offload, W1 R2)."""
        mock_urlopen.return_value = _chat_response("ok", "haervwe/GLM-4.6V-Flash-9B:latest")
        dispatch("haervwe/GLM-4.6V-Flash-9B:latest", "test")
        payload = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(payload["options"]["num_gpu"], 30)

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_glm_strips_begin_box_prefix(self, mock_urlopen):
        """GLM template leak: <|begin_of_box|> prefix must be stripped."""
        mock_urlopen.return_value = _chat_response(
            "<|begin_of_box|>bug", "haervwe/GLM-4.6V-Flash-9B:latest"
        )
        result = dispatch("haervwe/GLM-4.6V-Flash-9B:latest", "classify this")
        self.assertEqual(result["response"], "bug")

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_glm_clean_output_untouched(self, mock_urlopen):
        """GLM output without prefix passes through unchanged."""
        mock_urlopen.return_value = _chat_response(
            "clean response", "haervwe/GLM-4.6V-Flash-9B:latest"
        )
        result = dispatch("haervwe/GLM-4.6V-Flash-9B:latest", "test")
        self.assertEqual(result["response"], "clean response")


class TestQwenConfig(unittest.TestCase):

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_qwen_num_predict_2000(self, mock_urlopen):
        """Qwen must set num_predict=2000 for thinking-mode budget (W1 F001)."""
        mock_urlopen.return_value = _chat_response("ok", "qwen3.5:9b")
        dispatch("qwen3.5:9b", "test")
        payload = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(payload["options"]["num_predict"], 2000)

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_llama_no_num_predict(self, mock_urlopen):
        """Llama should NOT set num_predict (no thinking mode)."""
        mock_urlopen.return_value = _chat_response("ok", "llama3.2:3b")
        dispatch("llama3.2:3b", "test")
        payload = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertNotIn("num_predict", payload["options"])


class TestTemplateLeak(unittest.TestCase):

    def test_detect_begin_box(self):
        self.assertEqual(_check_template_leak("test <|begin_of_box|> leak"), "<|begin_of_box|>")

    def test_detect_im_start(self):
        self.assertEqual(_check_template_leak("<|im_start|>system"), "<|im_start|>")

    def test_clean_output(self):
        self.assertIsNone(_check_template_leak("just normal text"))

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_template_leak_sets_error_no_retry(self, mock_urlopen):
        """Template leak should set error and NOT retry (systemic issue)."""
        mock_urlopen.return_value = _chat_response(
            "leaked <|im_start|> token", "qwen3.5:9b"
        )
        result = dispatch("qwen3.5:9b", "test", max_retries=2)
        self.assertIn("template_leak", result["error"])
        self.assertEqual(result["retries_used"], 0)
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_template_leak_raises_when_configured(self, mock_urlopen):
        mock_urlopen.return_value = _chat_response(
            "leaked <|im_start|> token", "qwen3.5:9b"
        )
        with self.assertRaises(TemplateLeakError):
            dispatch("qwen3.5:9b", "test", raise_on_error=True)


class TestErrorTypes(unittest.TestCase):

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(MalformedResponseError, DispatchError))
        self.assertTrue(issubclass(TemplateLeakError, DispatchError))
        self.assertTrue(issubclass(ModelUnavailableError, DispatchError))
        self.assertTrue(issubclass(DispatchTimeoutError, DispatchError))

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_malformed_json_raises(self, mock_urlopen):
        resp = MagicMock()
        resp.read.return_value = b"not json at all"
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp
        with self.assertRaises(MalformedResponseError):
            dispatch("qwen3.5:9b", "test", raise_on_error=True, max_retries=0)

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_missing_message_content_raises(self, mock_urlopen):
        body = {"model": "qwen3.5:9b", "done": True}  # no message field
        resp = MagicMock()
        resp.read.return_value = json.dumps(body).encode("utf-8")
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp
        with self.assertRaises(MalformedResponseError):
            dispatch("qwen3.5:9b", "test", raise_on_error=True, max_retries=0)

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_404_raises_model_unavailable(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://localhost/api/chat", code=404, msg="Not Found",
            hdrs=None, fp=None,
        )
        with self.assertRaises(ModelUnavailableError):
            dispatch("nonexistent:1b", "test", raise_on_error=True)

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_timeout_raises_dispatch_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("timed out")
        with self.assertRaises(DispatchTimeoutError):
            dispatch("qwen3.5:9b", "test", raise_on_error=True, max_retries=0)


class TestRetryBackoff(unittest.TestCase):

    @patch("aho.pipeline.dispatcher.time.sleep")
    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_retries_on_connection_error(self, mock_urlopen, mock_sleep):
        """Connection errors should trigger retry with backoff."""
        import urllib.error
        mock_urlopen.side_effect = [
            urllib.error.URLError("connection refused"),
            urllib.error.URLError("connection refused"),
            _chat_response("ok"),
        ]
        result = dispatch("qwen3.5:9b", "test", max_retries=2, backoff_base=0.1)
        self.assertIsNone(result["error"])
        self.assertEqual(result["retries_used"], 2)
        self.assertEqual(mock_urlopen.call_count, 3)
        # Backoff: 0.1s, then 0.2s
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("aho.pipeline.dispatcher.time.sleep")
    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_no_retry_on_404(self, mock_urlopen, mock_sleep):
        """404 (model not found) should NOT retry — it's permanent."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=404, msg="Not Found", hdrs=None, fp=None,
        )
        result = dispatch("nonexistent:1b", "test", max_retries=2)
        self.assertIn("not found", result["error"].lower())
        self.assertEqual(mock_urlopen.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("aho.pipeline.dispatcher.time.sleep")
    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_exhausted_retries_returns_last_error(self, mock_urlopen, mock_sleep):
        mock_urlopen.side_effect = TimeoutError("timed out")
        result = dispatch("qwen3.5:9b", "test", max_retries=1, backoff_base=0.01)
        self.assertIn("timeout", result["error"])
        self.assertEqual(mock_urlopen.call_count, 2)  # initial + 1 retry


class TestParameterValidation(unittest.TestCase):

    def test_valid_num_ctx(self):
        self.assertEqual(_validate_num_ctx(32768), 32768)

    def test_clamp_low(self):
        self.assertEqual(_validate_num_ctx(100), MIN_NUM_CTX)

    def test_clamp_high(self):
        self.assertEqual(_validate_num_ctx(999999999), MAX_NUM_CTX)

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            _validate_num_ctx("not a number")

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            _validate_num_ctx(-1)

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_clamped_value_sent_to_ollama(self, mock_urlopen):
        mock_urlopen.return_value = _chat_response("ok")
        dispatch("qwen3.5:9b", "test", num_ctx=50)
        payload = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(payload["options"]["num_ctx"], MIN_NUM_CTX)


class TestResponseMetadata(unittest.TestCase):

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_family_in_result(self, mock_urlopen):
        mock_urlopen.return_value = _chat_response("ok", "llama3.2:3b")
        result = dispatch("llama3.2:3b", "test")
        self.assertEqual(result["family"], "llama3")

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_retries_used_in_result(self, mock_urlopen):
        mock_urlopen.return_value = _chat_response("ok")
        result = dispatch("qwen3.5:9b", "test")
        self.assertEqual(result["retries_used"], 0)


class TestModelManagement(unittest.TestCase):

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_unload_sends_keep_alive_zero(self, mock_urlopen):
        resp = MagicMock()
        resp.read.return_value = b"{}"
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp
        result = unload_model("nemotron-mini:4b")
        self.assertTrue(result)
        payload = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(payload["keep_alive"], 0)

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_list_loaded_models(self, mock_urlopen):
        body = {"models": [{"name": "qwen3.5:9b", "size_vram": 6000000000}]}
        resp = MagicMock()
        resp.read.return_value = json.dumps(body).encode("utf-8")
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp
        models = list_loaded_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["name"], "qwen3.5:9b")

    @patch("aho.pipeline.dispatcher.urllib.request.urlopen")
    def test_list_loaded_models_error_returns_empty(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")
        models = list_loaded_models()
        self.assertEqual(models, [])


class TestBackwardCompatibility(unittest.TestCase):

    def test_stop_tokens_constant_exists(self):
        """STOP_TOKENS module constant must still exist for old test imports."""
        self.assertEqual(STOP_TOKENS, ["<|endoftext|>", "<|im_end|>"])

    def test_default_num_ctx_constant(self):
        self.assertEqual(DEFAULT_NUM_CTX, 32768)


class TestPostprocessing(unittest.TestCase):

    def test_strip_begin_box(self):
        config = {"strip_prefix": "<|begin_of_box|>"}
        self.assertEqual(_postprocess_response("<|begin_of_box|>bug", config), "bug")

    def test_no_prefix_no_change(self):
        config = {"strip_prefix": None}
        self.assertEqual(_postprocess_response("clean", config), "clean")

    def test_prefix_not_present_no_change(self):
        config = {"strip_prefix": "<|begin_of_box|>"}
        self.assertEqual(_postprocess_response("no prefix here", config), "no prefix here")


if __name__ == "__main__":
    unittest.main()
