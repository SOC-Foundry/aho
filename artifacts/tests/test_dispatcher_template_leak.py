"""Tests for _check_template_leak normalization (0.2.16 W0, AF002).

0.2.15 W4 Gemini audit AF002: stage JSON emitted `template_leak_detected: null`
when `_check_template_leak` returned None on clean content. Fix: the detection
function returns False (not None) when clean, so stage JSON writers that emit
bool(leak) produce true/false not null/true.
"""
import unittest

from aho.pipeline.dispatcher import _check_template_leak


class TestCheckTemplateLeakReturnType(unittest.TestCase):

    def test_clean_content_returns_false_not_none(self):
        """Clean content → False (not None)."""
        result = _check_template_leak("This is normal content with no template tokens.")
        self.assertIs(result, False)
        self.assertIsNotNone(result)

    def test_empty_content_returns_false(self):
        """Empty string → False."""
        result = _check_template_leak("")
        self.assertIs(result, False)

    def test_glm_begin_box_leak_returns_token(self):
        """<|begin_of_box|> leak → returns that token string."""
        result = _check_template_leak("<|begin_of_box|>output here")
        self.assertEqual(result, "<|begin_of_box|>")

    def test_im_end_leak_returns_token(self):
        """<|im_end|> leak → returns that token string."""
        result = _check_template_leak("response<|im_end|>")
        self.assertEqual(result, "<|im_end|>")

    def test_bool_coercion_clean_is_false(self):
        """bool(result) is False for clean content → JSON emits 'false'."""
        self.assertFalse(bool(_check_template_leak("clean output")))

    def test_bool_coercion_leaked_is_true(self):
        """bool(result) is True for leaked content → JSON emits 'true'."""
        self.assertTrue(bool(_check_template_leak("<|im_end|>leaked")))

    def test_return_type_never_none(self):
        """Across a range of inputs, result is never None (AF002 contract)."""
        samples = [
            "",
            "plain",
            "multi\nline\ncontent",
            "<|begin_of_box|>leaked",
            "text with <|im_end|> leak",
            "   whitespace only   ",
        ]
        for s in samples:
            result = _check_template_leak(s)
            self.assertIsNotNone(result, f"Got None on input {s!r}")


if __name__ == "__main__":
    unittest.main()
