import re

from app.services.retrieval_service import RetrievedChunk


def rerank_chunks(
    query: str,
    chunks: list[RetrievedChunk]
) -> list[RetrievedChunk]:

    query_words = {
        word.lower().strip("¿?.,:;()[]{}")
        for word in query.split()
        if len(word.strip()) >= 4
    }

    wants_email = any(
        word in query.lower()
        for word in [
            "correo",
            "email",
            "e-mail",
            "electrónico"
        ]
    )

    email_pattern = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    reranked: list[RetrievedChunk] = []

    for chunk in chunks:

        content_lower = chunk.content.lower()

        keyword_matches = sum(
            1
            for word in query_words
            if word in content_lower
        )

        keyword_boost = keyword_matches * 0.05

        email_boost = 0.0

        if (
            wants_email
            and email_pattern.search(chunk.content)
        ):
            email_boost = 0.25

        final_score = (
            chunk.distance
            - keyword_boost
            - email_boost
        )

        reranked.append(
            chunk._replace(score=final_score)
        )

    return sorted(
        reranked,
        key=lambda chunk: chunk.score
    )