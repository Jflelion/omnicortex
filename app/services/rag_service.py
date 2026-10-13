from sqlalchemy.orm import Session

from app.observability.request_trace import RequestTrace
from app.services.llm_service import generate_answer
from app.services.prompt_builder import build_rag_prompt
from app.services.reranker_service import rerank_chunks
from app.services.retrieval_service import (
    RetrievedChunk,
    search_relevant_chunks,
)


def ask_question(
    question: str,
    user_id: int,
    db: Session,
    limit: int = 5
) -> tuple[str, list[RetrievedChunk]]:
    """
    Execute the complete RAG pipeline for an authenticated user.

    The function retrieves candidate chunks, reranks them, builds a grounded
    prompt, calls the configured language model, and returns the answer with
    its supporting sources.

    Each stage is measured through RequestTrace so the pipeline can report
    execution times and failures without coupling individual services to the
    observability layer.

    Args:
        question: Question submitted by the user.
        user_id: Identifier used to isolate documents owned by the user.
        db: Active SQLAlchemy database session.
        limit: Maximum number of chunks sent to the language model.

    Returns:
        A tuple containing the generated answer and the selected chunks.

    Raises:
        Exception: Re-raises any error produced by retrieval, reranking,
            prompt construction, or language-model generation.
    """

    trace = RequestTrace(
        operation="rag_question",
        user_id=user_id
    )

    try:
        trace.start_stage("retrieval")

        candidates = search_relevant_chunks(
            query=question,
            user_id=user_id,
            db=db,
            limit=limit * 3
        )

        trace.stop_stage("retrieval")

        trace.start_stage("reranking")

        chunks = rerank_chunks(
            query=question,
            chunks=candidates
        )[:limit]

        trace.stop_stage("reranking")

        trace.start_stage("prompt_builder")

        prompt = build_rag_prompt(
            question=question,
            chunks=chunks
        )

        trace.stop_stage("prompt_builder")

        trace.start_stage("llm")

        answer = generate_answer(prompt)

        trace.stop_stage("llm")
        trace.finish()

        return answer, chunks

    except Exception as error:
        trace.fail(error)
        raise