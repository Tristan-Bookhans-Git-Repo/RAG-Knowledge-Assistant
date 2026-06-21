import pytest

from app.services.parsers import parse

# ---------------------------------------------------------------------------
# TXT
# ---------------------------------------------------------------------------


def test_parse_txt_returns_content() -> None:
    assert parse(b"Hello world", "txt") == "Hello world"


def test_parse_txt_multiline() -> None:
    assert parse(b"Line 1\nLine 2", "txt") == "Line 1\nLine 2"


def test_parse_txt_case_insensitive() -> None:
    assert parse(b"hello", "TXT") == "hello"


# ---------------------------------------------------------------------------
# MD
# ---------------------------------------------------------------------------


def test_parse_md_returns_raw_text() -> None:
    data = b"# Title\n\nSome content"
    assert parse(data, "md") == "# Title\n\nSome content"


def test_parse_md_case_insensitive() -> None:
    assert parse(b"# hi", "MD") == "# hi"


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------


def test_parse_docx_returns_text(docx_bytes: bytes) -> None:
    result = parse(docx_bytes, "docx")
    assert "Hello DOCX" in result
    assert "Second paragraph" in result


def test_parse_docx_returns_string_type(docx_bytes: bytes) -> None:
    assert isinstance(parse(docx_bytes, "docx"), str)


def test_parse_docx_case_insensitive(docx_bytes: bytes) -> None:
    assert "Hello DOCX" in parse(docx_bytes, "DOCX")


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------


def test_parse_pdf_returns_string_type(pdf_bytes: bytes) -> None:
    assert isinstance(parse(pdf_bytes, "pdf"), str)


def test_parse_pdf_extracts_text(pdf_bytes: bytes) -> None:
    assert "Hello PDF" in parse(pdf_bytes, "pdf")


def test_parse_pdf_case_insensitive(pdf_bytes: bytes) -> None:
    assert isinstance(parse(pdf_bytes, "PDF"), str)


# ---------------------------------------------------------------------------
# Unsupported types
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("file_type", ["jpg", "png", "exe", "csv", "xlsx", "zip"])
def test_unsupported_type_raises(file_type: str) -> None:
    with pytest.raises(ValueError):
        parse(b"data", file_type)


def test_error_message_contains_supported_types() -> None:
    with pytest.raises(ValueError, match="pdf"):
        parse(b"data", "xyz")
