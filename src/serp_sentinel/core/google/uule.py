import base64

def encode_uule(canonical_name: str) -> str:
    raw=canonical_name.encode("utf-8")
    key="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"[len(raw)%64]
    payload=base64.urlsafe_b64encode(raw).decode().rstrip("=")
    return f"w+CAIQICI{key}{payload}"
