"""W8 acceptance: caption routing for document+caption messages."""
msg = {"text": "", "caption": "/ws last"}
text = msg.get("text", "") or msg.get("caption", "")
assert text == "/ws last", f"Expected '/ws last', got '{text}'"
assert text.startswith("/")
print("ok")
