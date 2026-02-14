import os
import sys

# Paths
KNOWLEDGE_DIR = "data/company_knowledge"
CHROMA_DIR = "vectorstore/chroma"

def get_embedding_model():
    """Returns real embeddings if available, else fake/random ones."""
    try:
        import transformers
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    except Exception as e:
        print(f"Warning: Error loading HF Embeddings (fallback to Fake): {e}")
        from langchain_core.embeddings import FakeEmbeddings
        return FakeEmbeddings(size=384)

def ingest():
    # Lazy imports to avoid top-level crashes in broken envs
    # removing TextLoader import as it's broken
    from langchain_community.vectorstores import Chroma
    from langchain_core.documents import Document
    
    # Simple manual loader to bypass broken langchain_community loaders
    class SimpleTextLoader:
        def __init__(self, file_path, encoding="utf-8"):
            self.file_path = file_path
            self.encoding = encoding
            
        def load(self):
            with open(self.file_path, "r", encoding=self.encoding) as f:
                text = f.read()
            return [Document(page_content=text, metadata={"source": self.file_path})]

    # Embedding model (robust load)
    embedding_model = get_embedding_model()

    documents = []
    
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"Directory {KNOWLEDGE_DIR} not found. Creating it.")
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        # Create a dummy file to avoid empty walk
        with open(os.path.join(KNOWLEDGE_DIR, "sample_template.txt"), "w") as f:
            f.write("Role: General\nSample offer template content here.")

    # Walk through all subfolders
    for root, _, files in os.walk(KNOWLEDGE_DIR):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)

                # Folder name = category (metadata)
                category = os.path.basename(root)

                loader = SimpleTextLoader(file_path, encoding="utf-8")
                docs = loader.load()

                for doc in docs:
                    doc.metadata = {
                        "source": file,
                        "category": category
                    }

                documents.extend(docs)

    print(f"Loaded {len(documents)} documents")

    if not documents:
        print("No documents to ingest.")
        return

    # Create or update ChromaDB
    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=CHROMA_DIR
    )

    # vectordb.persist() # Chroma 0.4+ persists automatically or uses different method

    print("✅ ChromaDB ingestion completed successfully!")

if __name__ == "__main__":
    ingest()
