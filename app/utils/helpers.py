import chromadb
import os
import json
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

# --- Database and Embedding Configuration ---

# Initialize a persistent ChromaDB client
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "db")
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)
client = chromadb.PersistentClient(path=DB_DIR)

# Initialize the sentence transformer model for embeddings
# Using a lightweight model for efficiency
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("SentenceTransformer model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load SentenceTransformer model: {e}", exc_info=True)
    embedding_model = None

# Get or create ChromaDB collections
document_collection = client.get_or_create_collection(name="flashlearn_documents")
subject_collection = client.get_or_create_collection(name="flashlearn_subjects")

# --- Text Processing ---

def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Splits a long text into smaller, overlapping chunks.
    """
    if not text:
        return []
    
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

# --- Database Operations ---

def upsert_document(subject: str, text_content: str):
    """
    Splits text into chunks, generates embeddings, and stores them in ChromaDB
    for RAG. Associates chunks with a subject.
    """
    if not embedding_model:
        raise RuntimeError("Embedding model is not available.")

    # First, clear any old chunks for this subject to avoid duplicates
    document_collection.delete(where={"subject": subject})
    logger.info(f"Cleared old document chunks for subject: {subject}")

    chunks = split_text_into_chunks(text_content)
    if not chunks:
        logger.warning(f"No text chunks to process for subject: {subject}")
        return

    embeddings = embedding_model.encode(chunks).tolist()
    ids = [f"{subject}_{i}" for i in range(len(chunks))]
    metadata = [{"subject": subject, "text": chunk} for chunk in chunks]

    document_collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadata
    )
    logger.info(f"Successfully added {len(chunks)} document chunks for subject: {subject}")

def save_learning_materials(subject: str, materials: dict):
    """
    Saves the generated summary, quiz, and flashcards for a given subject.
    The subject name is used as the ID.
    """
    # ChromaDB metadata values must be strings, numbers, or booleans.
    # We'll serialize the quiz and flashcards to JSON strings.
    metadata = {
        "summary": materials.get("summary", ""),
        "quiz": json.dumps(materials.get("quiz", [])),
        "flashcards": json.dumps(materials.get("flashcards", []))
    }

    # We use the subject as the ID. We need to provide a dummy embedding.
    # Since we won't search this collection by vector, it can be simple.
    dummy_embedding = [0] * embedding_model.get_sentence_embedding_dimension() if embedding_model else []


    subject_collection.upsert(
        ids=[subject],
        embeddings=[dummy_embedding],
        metadatas=[metadata]
    )
    logger.info(f"Saved learning materials for subject: {subject}")

def get_all_subjects() -> list[dict]:
    """
    Retrieves all unique subjects and their materials from the database.
    """
    results = subject_collection.get()    
    subjects = []
    for i, subject_id in enumerate(results['ids']):
        metadata = results['metadatas'][i]
        subjects.append({
            "name": subject_id,
            "summary": metadata.get("summary"),
            "quiz": json.loads(metadata.get("quiz", "[]")),
            "flashcards": json.loads(metadata.get("flashcards", "[]"))
        })
        
    return subjects

def get_subject_materials(subject: str) -> dict | None:
    """
    Retrieves the learning materials for a specific subject.
    """
    result = subject_collection.get(ids=[subject])
    if not result['ids']:
        return None
        
    metadata = result['metadatas'][0]
    return {
        "name": result['ids'][0],
        "summary": metadata.get("summary"),
        "quiz": json.loads(metadata.get("quiz", "[]")),
        "flashcards": json.loads(metadata.get("flashcards", "[]"))
    }

async def query_rag_for_answer(subject: str, question: str) -> str:
    """
    Finds relevant text chunks and uses the AI to generate an answer.
    """
    if not embedding_model:
        raise RuntimeError("Embedding model is not available.")

    # Find relevant document chunks for the given subject
    query_embedding = embedding_model.encode([question]).tolist()
    results = document_collection.query(
        query_embeddings=query_embedding,
        n_results=3,
        where={"subject": subject}
    )

    context_chunks = results['documents'][0]
    if not context_chunks:
        return "I couldn't find any relevant information in the documents for this subject to answer your question."

    context = "\n\n---\n\n".join(context_chunks)

    # Now, build a prompt for the AI
    prompt = f"""
    Based on the following context from the document, please answer the user's question.
    If the context does not contain the answer, say so.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    
    # We need to import the AI model here to avoid circular dependencies
    from app.services.ai_service import model
    
    if not model:
        raise RuntimeError("AI model is not available.")

    response = await model.generate_content_async(prompt)
    return response.text