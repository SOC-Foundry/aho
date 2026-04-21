"""Unit tests for aho.pipeline.router (0.2.15 W3).

Covers:
- Correct classification on clean model responses
- Bias string appended to system prompt
- Parse failure raises ClassificationError with raw response preserved
- Empty-categories guard
- Unknown model propagates ModelUnavailableError (no silent fallback)
- TimeoutError propagates DispatchTimeoutError
- Categories longer than one word match via substring
- System prompt includes category list verbatim
"""
import unittest
from unittest.mock import patch, MagicMock

from aho.pipeline.router import (
    classify_task,
    ClassificationError,
    _build_system_prompt,
    _match_category,
    DEFAULT_CLASSIFIER_MODEL,
)
from aho.pipeline.dispatcher import (
    DispatchError,
    ModelUnavailableError,
    DispatchTimeoutError,
    MalformedResponseError,
)


class TestBuildSystemPrompt(unittest.TestCase):

    def test_categories_listed_comma_separated(self):
        sp = _build_system_prompt(["bug", "feature"], None)
        self.assertIn("bug, feature", sp)
        self.assertIn("EXACTLY ONE", sp)
        self.assertIn("ONLY the category name", sp)

    def test_bias_appended_when_provided(self):
        sp = _build_system_prompt(["a", "b"], "prefer a for short inputs")
        self.assertIn("Bias:", sp)
        self.assertIn("prefer a for short inputs", sp)

    def test_bias_absent_when_none(self):
        sp = _build_system_prompt(["a", "b"], None)
        self.assertNotIn("Bias:", sp)


class TestMatchCategory(unittest.TestCase):

    def test_exact_match(self):
        self.assertEqual(_match_category("bug", ["bug", "feature"]), "bug")

    def test_leading_whitespace_stripped(self):
        self.assertEqual(_match_category(" bug", ["bug", "feature"]), "bug")

    def test_surrounding_quotes_stripped(self):
        self.assertEqual(_match_category("'feature'", ["bug", "feature"]), "feature")
        self.assertEqual(_match_category('"bug"', ["bug", "feature"]), "bug")

    def test_case_insensitive(self):
        self.assertEqual(_match_category("BUG", ["bug", "feature"]), "bug")
        self.assertEqual(_match_category("Feature", ["bug", "feature"]), "feature")

    def test_first_match_wins_on_substring(self):
        # "bug" appears in "debugger" — that is a known limitation of the
        # substring matcher, preserved from nemotron_client.classify() for
        # behavioural continuity. Documented so future callers know.
        self.assertEqual(_match_category("debugger", ["bug", "feature"]), "bug")

    def test_no_match_returns_none(self):
        self.assertIsNone(_match_category("something else entirely", ["bug", "feature"]))

    def test_empty_response_returns_none(self):
        self.assertIsNone(_match_category("", ["bug", "feature"]))


class TestClassifyTaskHappyPath(unittest.TestCase):

    @patch("aho.pipeline.router.dispatch")
    def test_classify_returns_matched_category(self, mock_dispatch):
        mock_dispatch.return_value = {
            "response": " feature",
            "error": None,
            "model": "nemotron-mini:4b",
        }
        result = classify_task("Add dark mode", ["bug", "feature"])
        self.assertEqual(result, "feature")

    @patch("aho.pipeline.router.dispatch")
    def test_classify_passes_expected_dispatch_kwargs(self, mock_dispatch):
        mock_dispatch.return_value = {"response": "bug", "error": None}
        classify_task("login broken", ["bug", "feature"], timeout=15, num_ctx=1024)
        kwargs = mock_dispatch.call_args.kwargs
        self.assertEqual(kwargs["timeout"], 15)
        self.assertEqual(kwargs["num_ctx"], 1024)
        self.assertEqual(kwargs["max_retries"], 0)
        self.assertTrue(kwargs["raise_on_error"])
        # positional model arg
        self.assertEqual(mock_dispatch.call_args.args[0], "nemotron-mini:4b")

    @patch("aho.pipeline.router.dispatch")
    def test_custom_model_override(self, mock_dispatch):
        mock_dispatch.return_value = {"response": "bug", "error": None}
        classify_task("x", ["bug", "feature"], model="custom:7b")
        self.assertEqual(mock_dispatch.call_args.args[0], "custom:7b")

    @patch("aho.pipeline.router.dispatch")
    def test_bias_threads_into_system_prompt(self, mock_dispatch):
        mock_dispatch.return_value = {"response": "assistant", "error": None}
        classify_task("hello", ["assistant", "code_runner"],
                      bias="prefer 'assistant' for general")
        system = mock_dispatch.call_args.kwargs["system"]
        self.assertIn("Bias:", system)
        self.assertIn("prefer 'assistant' for general", system)

    @patch("aho.pipeline.router.dispatch")
    def test_default_classifier_model_is_nemotron_mini(self, mock_dispatch):
        mock_dispatch.return_value = {"response": "bug", "error": None}
        classify_task("x", ["bug", "feature"])
        self.assertEqual(mock_dispatch.call_args.args[0], DEFAULT_CLASSIFIER_MODEL)
        self.assertEqual(DEFAULT_CLASSIFIER_MODEL, "nemotron-mini:4b")


class TestClassifyTaskErrors(unittest.TestCase):

    def test_empty_categories_raises_value_error(self):
        with self.assertRaises(ValueError):
            classify_task("x", [])

    @patch("aho.pipeline.router.dispatch")
    def test_unparseable_response_raises_classification_error(self, mock_dispatch):
        mock_dispatch.return_value = {
            "response": "(The Eleven Pillars Of Agile)",
            "error": None,
        }
        with self.assertRaises(ClassificationError) as ctx:
            classify_task("explain X", ["assistant", "code_runner", "reviewer"])
        self.assertEqual(ctx.exception.raw_response, "(The Eleven Pillars Of Agile)")
        self.assertEqual(
            ctx.exception.categories,
            ["assistant", "code_runner", "reviewer"],
        )

    @patch("aho.pipeline.router.dispatch")
    def test_empty_response_raises_classification_error(self, mock_dispatch):
        mock_dispatch.return_value = {"response": "", "error": None}
        with self.assertRaises(ClassificationError):
            classify_task("x", ["bug", "feature"])

    @patch("aho.pipeline.router.dispatch")
    def test_unknown_model_propagates_model_unavailable(self, mock_dispatch):
        mock_dispatch.side_effect = ModelUnavailableError(
            "Model 'nonexistent:99b' not found (HTTP 404)"
        )
        with self.assertRaises(ModelUnavailableError):
            classify_task("x", ["a", "b"], model="nonexistent:99b")

    @patch("aho.pipeline.router.dispatch")
    def test_timeout_propagates_dispatch_timeout(self, mock_dispatch):
        mock_dispatch.side_effect = DispatchTimeoutError("timeout after 30s")
        with self.assertRaises(DispatchTimeoutError):
            classify_task("x", ["a", "b"])

    @patch("aho.pipeline.router.dispatch")
    def test_malformed_response_propagates(self, mock_dispatch):
        mock_dispatch.side_effect = MalformedResponseError("bad json")
        with self.assertRaises(MalformedResponseError):
            classify_task("x", ["a", "b"])


class TestClassificationErrorShape(unittest.TestCase):

    def test_subclass_of_dispatch_error(self):
        self.assertTrue(issubclass(ClassificationError, DispatchError))

    def test_stores_raw_response_and_categories(self):
        err = ClassificationError("no match", raw_response="prose drift",
                                   categories=["a", "b"])
        self.assertEqual(err.raw_response, "prose drift")
        self.assertEqual(err.categories, ["a", "b"])

    def test_defaults_when_optional_args_missing(self):
        err = ClassificationError("no match")
        self.assertEqual(err.raw_response, "")
        self.assertEqual(err.categories, [])


if __name__ == "__main__":
    unittest.main()
