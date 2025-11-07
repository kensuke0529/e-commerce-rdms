from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os
import chromadb
from pathlib import Path

# Import LangSmith configuration to enable tracing
from ..langsmith_config import setup_langsmith

load_dotenv()
setup_langsmith()

# Hardcoded paths
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent.parent
_chroma_db_path = _project_root / "result" / "chroma_db"
_chroma_db_path.mkdir(parents=True, exist_ok=True)

RETURN_POLICY_PDF = _project_root / "documents" / "return_policy.pdf"
SHIPPING_POLICY_PDF = _project_root / "documents" / "shipping_policy.pdf"
COLLECTION_NAME = "policy_docs"

# Initialize Chroma client
chroma_client = chromadb.PersistentClient(path=str(_chroma_db_path))

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small", openai_api_key=os.environ.get("OPENAI_API_KEY")
)


def add_pdf_to_collection(
    file_path: Path, chunk_size: int = 500, chunk_overlap: int = 50
):
    """Add a PDF file to the embeddings collection"""
    # Load PDF
    loader = PyPDFLoader(str(file_path))
    pages = list(loader.lazy_load())
    all_text = "\n".join(page.page_content for page in pages)

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    texts = text_splitter.split_text(all_text)

    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    embeddings = embedding_model.embed_documents(texts)

    # Add to ChromaDB in batches
    batch_size = 100
    doc_count = collection.count()

    for batch_idx in range(0, len(texts), batch_size):
        batch_texts = texts[batch_idx : batch_idx + batch_size]
        batch_embeddings = embeddings[batch_idx : batch_idx + batch_size]
        batch_ids = [
            f"doc_{doc_count + batch_idx + doc_idx}"
            for doc_idx in range(len(batch_texts))
        ]
        collection.add(
            ids=batch_ids, documents=batch_texts, embeddings=batch_embeddings
        )

    print(
        f"Successfully added {len(texts)} documents to collection '{COLLECTION_NAME}'"
    )
    return len(texts)


if __name__ == "__main__":
    # Add both PDFs to the same collection
    add_pdf_to_collection(RETURN_POLICY_PDF)
    add_pdf_to_collection(SHIPPING_POLICY_PDF)


# Query function to retrieve similar chunks from the collection
def query_policies_docs(
    query_text: str,
    n_results: int = 3,
    limit: int = None,
):
    if not query_text or not query_text.strip():
        return []

    # Use limit if provided, otherwise use n_results
    if limit is not None:
        n_results = limit

    # Get the collection
    try:
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
    except Exception:
        print(
            f"Collection '{COLLECTION_NAME}' does not exist. Please add documents first."
        )
        return []

    count = collection.count()
    if count == 0:
        return []

    # Generate query embedding and query
    query_embedding = embedding_model.embed_query(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, count),
        include=["documents", "distances", "metadatas"],
    )

    documents = results.get("documents", [])
    return (
        documents[0]
        if documents and len(documents) > 0 and len(documents[0]) > 0
        else []
    )
