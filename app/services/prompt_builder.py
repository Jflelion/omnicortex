from typing import Any


def build_rag_prompt(
    question: str,
    chunks: list[Any]
) -> str:
    context_parts: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[Chunk {index}]\n{chunk.content}"
        )

    context = "\n\n".join(context_parts)

    return f"""
Eres un asistente de IA especializado en responder preguntas usando documentos.

Debes responder usando únicamente el CONTEXTO proporcionado.
Si la respuesta aparece en el contexto, respóndela directamente.
Si hay correos, nombres, teléfonos o fechas, extráelos literalmente.
Si la respuesta no aparece en el contexto, responde:
"No tengo suficiente información en los documentos proporcionados."

CONTEXTO:
{context}

PREGUNTA:
{question}

RESPUESTA:
""".strip()