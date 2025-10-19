def sanitize_filename(name: str) -> str:
    """Sanitize string to safe filename."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    return name.strip()