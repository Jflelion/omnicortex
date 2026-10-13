import pytest

from app.services.text_chunker import chunk_text


def test_short_text_returns_single_chunk():
    assert chunk_text("hola mundo", chunk_size=100, overlap=10) == ["hola mundo"]


def test_empty_text_returns_no_chunks():
    assert chunk_text("", chunk_size=100, overlap=10) == []


def test_chunks_respect_size_and_overlap():
    text = "".join(str(i % 10) for i in range(250))

    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert [len(chunk) for chunk in chunks] == [100, 100, 90, 10]
    assert chunks[0][-20:] == chunks[1][:20]
    assert chunks[1][-20:] == chunks[2][:20]


def test_chunks_cover_all_text():
    text = "abcdefghij" * 37

    chunks = chunk_text(text, chunk_size=50, overlap=10)

    rebuilt = chunks[0] + "".join(chunk[10:] for chunk in chunks[1:])
    assert rebuilt == text


@pytest.mark.parametrize("overlap", [100, 150])
def test_overlap_must_be_smaller_than_chunk_size(overlap: int):
    with pytest.raises(ValueError):
        chunk_text("texto", chunk_size=100, overlap=overlap)
