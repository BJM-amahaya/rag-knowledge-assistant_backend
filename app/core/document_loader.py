from langchain_core.documents import Document
from pypdf import PdfReader


def load_document(file_path: str) -> list[Document]:
    """PDFファイルからテキストを抽出し、Documentオブジェクトのリストを返す。"""
    reader = PdfReader(file_path)
    documents = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": file_path, "page": i + 1},
                )
            )

    return documents
