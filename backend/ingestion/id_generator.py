import hashlib
from pathlib import Path


def generate_document_id(
    source: str,
    relative_path: Path,
) -> str:

    normalized_path = relative_path.as_posix().lower()

    identity = f"{source.lower()}:{normalized_path}"

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()