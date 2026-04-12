with open("src/aho/council/inventory.py", "r") as f:
    content = f.read()

content = content.replace(
    'status="operational" if "qwen" in str(name).lower() or "nemoclaw" in str(name).lower() else "unknown"',
    'status="unknown"'
)

new_return = '''    for member in members:
        if "qwen" in member.name.lower() or "nemoclaw" in member.name.lower():
            member.status = "operational"

    return members'''

content = content.replace("    return members", new_return)

with open("src/aho/council/inventory.py", "w") as f:
    f.write(content)
