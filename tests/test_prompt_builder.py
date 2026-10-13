from types import SimpleNamespace

from app.services.prompt_builder import build_rag_prompt


def test_prompt_contains_question_and_numbered_chunks():
    chunks = [
        SimpleNamespace(content="Primer fragmento"),
        SimpleNamespace(content="Segundo fragmento"),
    ]

    prompt = build_rag_prompt("¿Qué dice el documento?", chunks)

    assert "[Chunk 1]\nPrimer fragmento" in prompt
    assert "[Chunk 2]\nSegundo fragmento" in prompt
    assert prompt.index("CONTEXTO:") < prompt.index("[Chunk 1]")
    assert prompt.index("PREGUNTA:\n¿Qué dice el documento?") > prompt.index("[Chunk 2]")
    assert prompt.endswith("RESPUESTA:")


def test_prompt_includes_fallback_instruction():
    prompt = build_rag_prompt("pregunta", [])

    assert "No tengo suficiente información" in prompt
