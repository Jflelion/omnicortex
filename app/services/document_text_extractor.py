from pathlib import Path
from typing import cast

import fitz  # pyright: ignore[reportMissingTypeStubs]


def extract_text_from_pdf(
    file_path: str
) -> str:
    """
    Extract text from a PDF file using PyMuPDF.
    """

    path = Path(file_path)

    if not path.exists():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    text_parts: list[str] = []

    with fitz.open(path) as document:

        for page in document:

            page_text = cast(
                str,
                page.get_text() # pyright: ignore[reportUnknownMemberType]
            )

            text_parts.append(page_text)

    return "\n".join(text_parts).strip()