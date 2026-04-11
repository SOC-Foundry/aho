"""Streaming Qwen client with heartbeat and repetition detection.

aho 0.1.7 W1: replaced the non-streaming blocking implementation
with token-by-token streaming, 30-second elapsed-time heartbeats,
and a rolling-window repetition detector that kills degenerate
generation loops within seconds instead of minutes.
"""
import json
import sys
import time
from typing import Optional

import requests

from aho.artifacts.repetition_detector import RepetitionDetector, DegenerateGenerationError
from aho.logger import log_event


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_TIMEOUT = 600  # was 1800 in 0.1.4, reduced after 0.1.6 audit
DEFAULT_NUM_CTX = 16384  # was 8192 in 0.1.4, bumped for long-form generation
HEARTBEAT_INTERVAL_S = 30


class QwenClient:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
        num_ctx: int = DEFAULT_NUM_CTX,
        temperature: float = 0.2,
        verbose: bool = True,
    ):
        self.model = model
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.temperature = temperature
        self.verbose = verbose

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        json_format: bool = False,
    ) -> str:
        """Generate a response via streaming with heartbeat and repetition detection.

        Returns the complete response as a string. Raises DegenerateGenerationError
        if repetition detector fires. Raises requests.Timeout if the whole generation
        exceeds self.timeout.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_ctx": self.num_ctx,
                "temperature": self.temperature,
            },
        }
        if system:
            payload["system"] = system
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        if json_format:
            payload["format"] = "json"

        accumulated = []
        thinking_accumulated = []
        detector = RepetitionDetector(window_size=200, similarity_threshold=0.70)
        thinking_detector = RepetitionDetector(window_size=200, similarity_threshold=0.65)
        start = time.monotonic()
        last_heartbeat = start
        token_count = 0
        thinking_token_count = 0
        check_interval = 50  # check repetition every N tokens

        if self.verbose:
            print(f"[qwen] starting generation (model={self.model}, timeout={self.timeout}s)", file=sys.stderr, flush=True)

        try:
            with requests.post(OLLAMA_URL, json=payload, timeout=self.timeout, stream=True) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    token = chunk.get("response", "")
                    thinking = chunk.get("thinking", "")
                    
                    if thinking:
                        thinking_accumulated.append(thinking)
                        thinking_token_count += 1
                        if self.verbose:
                            sys.stderr.write(thinking)
                            sys.stderr.flush()
                        # Check thinking tokens for degenerate loops
                        if thinking_token_count % check_interval == 0:
                            thinking_detector.add_tokens(thinking_accumulated[-check_interval:])
                            if thinking_detector.check():
                                log_event("repetition_detected", "repetition-detector",
                                          self.model, "check",
                                          output_summary=f"thinking_token_count={thinking_token_count}",
                                          status="failed")
                                raise DegenerateGenerationError(
                                    f"Thinking repetition detected at token {thinking_token_count}, {int(time.monotonic() - start)}s elapsed",
                                    sample=thinking_detector.get_sample(),
                                    total_tokens=thinking_token_count,
                                )

                    if token:
                        accumulated.append(token)
                        token_count += 1

                        # Stream token to stderr if verbose
                        if self.verbose:
                            sys.stderr.write(token)
                            sys.stderr.flush()

                        # Heartbeat check
                        now = time.monotonic()
                        if now - last_heartbeat >= HEARTBEAT_INTERVAL_S:
                            elapsed = int(now - start)
                            words = len("".join(accumulated).split())
                            if self.verbose:
                                print(
                                    f"\n[qwen] heartbeat: {elapsed}s elapsed, {token_count} tokens, {words} words so far",
                                    file=sys.stderr,
                                    flush=True,
                                )
                            last_heartbeat = now

                        # Repetition check every N tokens
                        if token_count % check_interval == 0:
                            detector.add_tokens(accumulated[-check_interval:])
                            if detector.check():
                                log_event("repetition_detected", "repetition-detector",
                                          self.model, "check",
                                          output_summary=f"token_count={token_count}",
                                          status="failed")
                                raise DegenerateGenerationError(
                                    f"Repetition detected at token {token_count}, {int(time.monotonic() - start)}s elapsed",
                                    sample=detector.get_sample(),
                                    total_tokens=token_count,
                                )

                    if chunk.get("done"):
                        break

        except requests.Timeout as e:
            elapsed = int(time.monotonic() - start)
            log_event(
                event_type="llm_call",
                source_agent="qwen-client",
                target=self.model,
                action="generate",
                input_summary=prompt,
                status="timeout",
                error=str(e),
                latency_ms=elapsed * 1000
            )
            if self.verbose:
                print(f"\n[qwen] TIMEOUT after {elapsed}s, {token_count} tokens generated", file=sys.stderr)
            raise
        except DegenerateGenerationError as e:
            elapsed = int(time.monotonic() - start)
            log_event(
                event_type="llm_call",
                source_agent="qwen-client",
                target=self.model,
                action="generate",
                input_summary=prompt,
                output_summary=e.sample,
                status="failed",
                error=str(e),
                latency_ms=elapsed * 1000,
                gotcha_triggered="aho-G015" # Degenerate repetition
            )
            raise
        except Exception as e:
            elapsed = int(time.monotonic() - start)
            log_event(
                event_type="llm_call",
                source_agent="qwen-client",
                target=self.model,
                action="generate",
                input_summary=prompt,
                status="error",
                error=str(e),
                latency_ms=elapsed * 1000
            )
            raise

        elapsed = int(time.monotonic() - start)
        full_text = "".join(accumulated)
        word_count = len(full_text.split())

        log_event(
            event_type="llm_call",
            source_agent="qwen-client",
            target=self.model,
            action="generate",
            input_summary=prompt,
            output_summary=full_text,
            status="success",
            tokens={"total": token_count},
            latency_ms=elapsed * 1000
        )

        if self.verbose:
            print(
                f"\n[qwen] done: {elapsed}s elapsed, {token_count} tokens, {word_count} words",
                file=sys.stderr,
                flush=True,
            )

        return full_text
