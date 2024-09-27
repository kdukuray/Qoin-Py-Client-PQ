import base64


def binary_to_b64(binary_str: bytes) -> str:
    """Converts binary data into base64"""
    return base64.b64encode(binary_str).decode("utf-8")


def b64_to_binary(b64_str: str) -> bytes:
    """Converts base64 strings in binary data"""
    return base64.b64decode(b64_str.encode("utf-8"))
