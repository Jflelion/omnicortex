def chunk_text(
    text: str,
    chunk_size: int,
    overlap: int
) -> list[str]:
    """
    Split text into overlapping chunks.
    """

    if chunk_size <= overlap:
        raise ValueError(
            "chunk_size must be greater than overlap"
        )

    chunks: list[str] = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks