from app.services.chunker import chunk

# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_string_returns_empty_list() -> None:
    assert chunk("") == []


def test_whitespace_only_returns_empty_list() -> None:
    assert chunk("   ") == []


def test_short_text_returns_single_chunk() -> None:
    result = chunk("Short text.")
    assert len(result) == 1
    assert result[0] == "Short text."


# ---------------------------------------------------------------------------
# Chunking behaviour
# ---------------------------------------------------------------------------


def test_long_text_returns_multiple_chunks() -> None:
    text = "a" * 600
    result = chunk(text)
    assert len(result) >= 2


def test_all_chunks_are_strings() -> None:
    text = "word " * 200
    result = chunk(text)
    assert all(isinstance(c, str) for c in result)


def test_chunks_do_not_exceed_chunk_size() -> None:
    text = "word " * 200
    for c in chunk(text):
        assert len(c) <= 512


def test_overlap_is_applied() -> None:
    text = "a" * 475 + "b" * 125
    result = chunk(text)
    assert len(result) == 2
    tail_of_first = result[0][-50:]
    head_of_second = result[1][:50]
    assert tail_of_first == head_of_second


def test_each_chunk_is_substring_of_original() -> None:
    text = "Hello world. " * 100
    for c in chunk(text):
        assert c in text


def test_returns_list() -> None:
    assert isinstance(chunk("some text"), list)
