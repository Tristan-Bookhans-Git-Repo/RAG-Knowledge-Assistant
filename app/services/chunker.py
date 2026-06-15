from langchain_text_splitters import RecursiveCharacterTextSplitter

_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)


def chunk(text: str) -> list[str]:
    if not text:
        return []
    return _splitter.split_text(text)
