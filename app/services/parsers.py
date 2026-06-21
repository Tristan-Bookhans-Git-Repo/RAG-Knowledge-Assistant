import io

from docx import Document
from pypdf import PdfReader

SUPPORTED_TYPES = frozenset({"pdf", "docx", "txt", "md"})


class UnsupportedFileTypeError(ValueError):
    pass


def parse(file_bytes: bytes, file_type: str) -> str:
    match file_type.lower():
        case "pdf":
            return _parse_pdf(file_bytes)
        case "docx":
            return _parse_docx(file_bytes)
        case "txt" | "md":
            return file_bytes.decode("utf-8")
        case _:
            raise UnsupportedFileTypeError(
                f"Unsupported file type: {file_type!r}. "
                + f"Supported: {', '.join(sorted(SUPPORTED_TYPES))}"
            )


def _parse_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    return "\n".join(para.text for para in doc.paragraphs)
