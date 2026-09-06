"""FNV-1a 32-bit, hex. A room handle, not a crypto hash."""


def digest(bytes_: str) -> str:
    h = 2166136261
    for ch in bytes_:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return f"{h:08x}"
