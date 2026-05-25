import os
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from pypdf import PdfReader

KB_DIR = os.getenv("KB_DIR", str(Path(__file__).parent / "knowledge_base"))
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", str(Path(__file__).parent / "vector_store"))
LINKEDIN_PDF = os.getenv("LINKEDIN_PDF", str(Path(__file__).parent / "me" / "linkedin.pdf"))
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = int(os.getenv("TOP_K", "5"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.25"))

_embeddings: Optional[HuggingFaceEmbeddings] = None
_vectorstore: Optional[Chroma] = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return _embeddings


def _load_linkedin_text() -> str:
    pdf_path = Path(LINKEDIN_PDF)
    if not pdf_path.exists():
        return ""
    reader = PdfReader(str(pdf_path))
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text.strip()


def _build_vectorstore() -> Chroma:
    docs = []
    loader = DirectoryLoader(
        KB_DIR,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=False,
    )
    docs.extend(loader.load())

    linkedin_text = _load_linkedin_text()
    if linkedin_text:
        from langchain_community.document_loaders import TextLoader as TL
        from langchain_core.documents import Document
        docs.append(Document(page_content=linkedin_text, metadata={"source": "linkedin.pdf"}))

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    vs = Chroma.from_documents(
        documents=chunks,
        embedding=_get_embeddings(),
        persist_directory=VECTOR_STORE_DIR,
    )
    print(f"[rag] built vector store — {len(chunks)} chunks from {len(docs)} documents")
    return vs


def _load_vectorstore() -> Chroma:
    return Chroma(
        persist_directory=VECTOR_STORE_DIR,
        embedding_function=_get_embeddings(),
    )


def init_rag(force_rebuild: bool = False) -> None:
    global _vectorstore
    store_exists = (
        Path(VECTOR_STORE_DIR).exists()
        and any(Path(VECTOR_STORE_DIR).iterdir())
    )
    if force_rebuild or not store_exists:
        _vectorstore = _build_vectorstore()
    else:
        _vectorstore = _load_vectorstore()
        print(f"[rag] loaded existing vector store from {VECTOR_STORE_DIR}")


def retrieve_context(query: str, top_k: int = TOP_K) -> list[str]:
    global _vectorstore
    if _vectorstore is None:
        init_rag()
    retriever = _vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": top_k, "score_threshold": SCORE_THRESHOLD},
    )
    docs = retriever.invoke(query)
    return [d.page_content for d in docs]
