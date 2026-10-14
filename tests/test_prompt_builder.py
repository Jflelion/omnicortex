from types import SimpleNamespace

from app.services.prompt_builder import HistoryTurn, build_rag_prompt


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


def test_prompt_includes_history_before_question():
    history = [
        HistoryTurn("user", "¿Quién es la gerente?"),
        HistoryTurn("assistant", "Ana Pérez."),
    ]

    prompt = build_rag_prompt("¿Y su teléfono?", [], history)

    assert "Usuario: ¿Quién es la gerente?\nAsistente: Ana Pérez." in prompt
    assert prompt.index("CONTEXTO:") < prompt.index("HISTORIAL") < prompt.index("PREGUNTA:")


def test_prompt_without_history_has_no_history_section():
    assert "HISTORIAL" not in build_rag_prompt("pregunta", [])
