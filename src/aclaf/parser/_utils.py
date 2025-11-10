def full_option_name(name: str) -> str:
    if len(name) == 1:
        return f"-{name}"
    return f"--{name}"
