import secrets


def generate_verification_code() -> str:
    """Generate a 4-digit verification code."""
    return f"{secrets.randbelow(10000):04d}"
