from collections.abc import Sequence
from typing import Any, NamedTuple


class HistoryTurn(NamedTuple):
    role: str
    content: str


ROLE_LABELS = {
    "user": "Usuario",
    "assistant": "Asistente",
}


def build_rag_prompt(
    question: str,
    chunks: list[Any],
    history: Sequence[HistoryTurn] = ()
) -> str:
    context_parts: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[Chunk {index}]\n{chunk.content}"
        )

    context = "\n\n".join(context_parts)

    history_section = ""

    if history:
        history_lines = "\n".join(
            f"{ROLE_LABELS.get(turn.role, turn.role)}: {turn.content}"
            for turn in history
        )

        history_section = f"""
HISTORIAL DE LA CONVERSACIÓN (úsalo solo para entender a qué se refiere la pregunta):
{history_lines}
"""

    return f"""
Eres un asistente de IA especializado en responder preguntas usando documentos.

Debes responder usando únicamente el CONTEXTO proporcionado.
Si la respuesta aparece en el contexto, respóndela directamente.
Si hay correos, nombres, teléfonos o fechas, extráelos literalmente.
Si la respuesta no aparece en el contexto, responde:
"No tengo suficiente información en los documentos proporcionados."

CONTEXTO:
{context}
{history_section}
PREGUNTA:
{question}

RESPUESTA:
""".strip()
