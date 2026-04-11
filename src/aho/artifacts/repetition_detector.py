"""Rolling-window repetition detector for LLM generation.

Addresses the 0.1.5 failure mode where Qwen entered a repetition loop
in the plan document's footer and generated the same 12-line block
fifteen-plus times before truncation. See aho 0.1.7 design Appendix A.
"""
from difflib import SequenceMatcher
import re
from typing import Optional


class DegenerateGenerationError(Exception):
    """Raised when a generation appears to be in a repetition loop."""

    def __init__(self, message: str, sample: Optional[str] = None, total_tokens: int = 0):
        super().__init__(message)
        self.sample = sample
        self.total_tokens = total_tokens


class RepetitionDetector:
    """Detects degenerate repetition in streaming LLM output.

    Uses a rolling window: compares the last `window_size` tokens against
    the preceding `window_size` tokens using character-level sequence
    similarity. If the ratio exceeds `similarity_threshold`, the generation
    is considered degenerate.

    Also includes a density check: if the variety of unique words in a
    larger window falls below a threshold, it flags the generation as
    stalled or looping.
    """

    def __init__(self, window_size: int = 200, similarity_threshold: float = 0.70):
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self._buffer: list[str] = []

    def add_tokens(self, tokens: list[str]) -> None:
        self._buffer.extend(tokens)
        # Keep enough for both checks
        max_keep = max(self.window_size * 2 + 50, 1000)
        if len(self._buffer) > max_keep:
            self._buffer = self._buffer[-max_keep:]

    def check(self) -> bool:
        """Return True if the generation appears degenerate."""
        # 1. Structural repetition (N-gram-ish)
        if len(self._buffer) >= 2 * self.window_size:
            recent = "".join(self._buffer[-self.window_size:])
            previous = "".join(self._buffer[-2 * self.window_size:-self.window_size])

            if recent and previous:
                ratio = SequenceMatcher(None, recent, previous).ratio()
                if ratio >= self.similarity_threshold:
                    return True

        # 2. Information density (unique words ratio)
        # Check a 500-token window if we have it
        density_window = 500
        if len(self._buffer) >= density_window:
            # Join with space to ensure re.findall picks up individual words
            # even if tokens themselves don't have spaces.
            text = " ".join(self._buffer[-density_window:]).lower()
            words = re.findall(r"\w+", text)
            if len(words) >= 50: # Only check if we have enough words to be statistically useful
                unique_words = set(words)
                density = len(unique_words) / len(words)
                if density < 0.10: # Threshold: less than 10% unique words (tightened from 0.15)
                    return True

        return False

    def get_sample(self) -> str:
        """Return a sample of the repeating content for diagnostic logs."""
        if len(self._buffer) < self.window_size:
            return "".join(self._buffer)
        return "".join(self._buffer[-self.window_size:])
