from app.services.reranker_service import rerank_chunks
from app.services.retrieval_service import RetrievedChunk


def make_chunk(chunk_id: int, content: str, distance: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=1,
        chunk_index=chunk_id,
        content=content,
        distance=distance,
        score=distance
    )


def test_keyword_matches_move_chunk_up():
    far_with_keywords = make_chunk(1, "El contrato de arrendamiento vence en marzo", 0.40)
    close_without_keywords = make_chunk(2, "Texto sin relación", 0.35)

    result = rerank_chunks(
        "¿Cuándo vence el contrato de arrendamiento?",
        [close_without_keywords, far_with_keywords]
    )

    assert [chunk.chunk_id for chunk in result] == [1, 2]


def test_email_question_boosts_chunks_with_email():
    with_email = make_chunk(1, "Contacto: soporte@omnicortex.dev", 0.60)
    without_email = make_chunk(2, "Información general", 0.40)

    result = rerank_chunks("¿Cuál es el correo?", [without_email, with_email])

    assert result[0].chunk_id == 1
    assert result[0].score == 0.60 - 0.25


def test_keeps_original_distance_and_computes_score():
    chunk = make_chunk(1, "nada relevante", 0.30)

    [result] = rerank_chunks("pregunta cualquiera", [chunk])

    assert result.distance == 0.30
    assert result.score == 0.30


def test_empty_input():
    assert rerank_chunks("pregunta", []) == []
