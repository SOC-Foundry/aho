import re

# Regex patterns for common secret formats in fish config: set -x NAME "VALUE"
PATTERNS = [
    re.compile(r'set -gx (\w+_API_KEY) "([^"]+)"'),
    re.compile(r'set -gx (\w+_TOKEN) "([^"]+)"'),
    re.compile(r'set -gx (\w+_SECRET) "([^"]+)"'),
    re.compile(r'set -gx (\w+_BOT_TOKEN) "([^"]+)"'),
    re.compile(r'set -x (\w+_API_KEY) "([^"]+)"'),
    re.compile(r'set -x (\w+_TOKEN) "([^"]+)"'),
    re.compile(r'set -x (\w+_SECRET) "([^"]+)"'),
    re.compile(r'set -x (\w+_BOT_TOKEN) "([^"]+)"'),
]
