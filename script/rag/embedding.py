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

# Hardcoded paths - works in Docker and deployed environments
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent.parent
_chroma_db_path = _project_root / "result" / "chroma_db"
_chroma_db_path.mkdir(parents=True, exist_ok=True)

RETURN_POLICY_PDF = _project_root / "documents" / "return_policy.pdf"
SHIPPING_POLICY_PDF = _project_root / "documents" / "shipping_policy.pdf"
COLLECTION_NAME = "policy_docs"

# Log paths for debugging (useful in Docker/Render)
print(f"RAG Configuration:")
print(f"  Project root: {_project_root}")
print(f"  ChromaDB path: {_chroma_db_path}")
print(
    f"  Return policy PDF: {RETURN_POLICY_PDF} (exists: {RETURN_POLICY_PDF.exists()})"
)
print(
    f"  Shipping policy PDF: {SHIPPING_POLICY_PDF} (exists: {SHIPPING_POLICY_PDF.exists()})"
)

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


# Initialize RAG collection lazily (only when needed)
def _initialize_rag_collection_if_needed():
    """Initialize RAG collection with PDFs if it doesn't exist or is empty"""
    try:
        collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        count = collection.count()

        # If collection is empty, load PDFs
        if count == 0:
            print("RAG collection is empty. Initializing with PDF documents...")
            if RETURN_POLICY_PDF.exists():
                add_pdf_to_collection(RETURN_POLICY_PDF)
            else:
                print(f"Warning: Return policy PDF not found at {RETURN_POLICY_PDF}")

            if SHIPPING_POLICY_PDF.exists():
                add_pdf_to_collection(SHIPPING_POLICY_PDF)
            else:
                print(
                    f"Warning: Shipping policy PDF not found at {SHIPPING_POLICY_PDF}"
                )

            print("RAG collection initialized successfully.")
            return True
        else:
            # Collection already has data - no need to reload
            return False
    except Exception as e:
        print(f"Error initializing RAG collection: {e}")
        return False


# Note: We don't initialize on import - only when first query is made
# This improves startup performance


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

    # Get the collection (will auto-create if needed)
    try:
        collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error getting collection: {e}")
        return []

    count = collection.count()
    if count == 0:
        # Lazy initialization: Only load PDFs when first query is made
        print("Collection is empty, initializing on first query...")
        _initialize_rag_collection_if_needed()
        # Re-fetch collection after initialization
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        count = collection.count()
        if count == 0:
            print("RAG collection is still empty after initialization attempt.")
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
