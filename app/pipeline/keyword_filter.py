def passes_filter(text: str, rules: dict) -> bool:
    lower = text.lower()
    for word in rules.get("exclude", []):
        if word.lower() in lower:
            return False
    include = rules.get("include", [])
    if not include:
        return True
    return any(word.lower() in lower for word in include)
