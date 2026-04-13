with open("src/aho/council/inventory.py", "r") as f:
    content = f.read()

new_return = '''    for member in members:
        if "qwen" in member.name.lower() or "nemoclaw" in member.name.lower():
            member.status = "operational"
        elif "evaluator" in member.name.lower() or "glm" in member.name.lower():
            member.status = "gap: parsing logic converts real reviews to rubber stamps"

    return members'''

content = content.replace('''    for member in members:
        if "qwen" in member.name.lower() or "nemoclaw" in member.name.lower():
            member.status = "operational"

    return members''', new_return)

with open("src/aho/council/inventory.py", "w") as f:
    f.write(content)
