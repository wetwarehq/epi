"""FNV-1a 32-bit of the UTF-8 bytes, hex. A room handle, not a crypto hash."""


def digest(bytes_: str) -> str:
    h = 2166136261
    for b in bytes_.encode("utf-8"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return f"{h:08x}"
