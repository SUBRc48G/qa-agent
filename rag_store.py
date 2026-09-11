from sentence_transformers import SentenceTransformer
import chromadb
from qa_kb import qa_examples

# ---------------- MODEL ----------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# ---------------- VECTOR DB ----------------
client = chromadb.Client()
collection = client.get_or_create_collection("qa_kb")

# ---------------- LOAD DATA ----------------
for i, item in enumerate(qa_examples):
    embedding = model.encode(item["input"]).tolist()

    collection.add(
        ids=[str(i)],
        embeddings=[embedding],
        documents=[item["output"]]
    )

# ---------------- RETRIEVAL FUNCTION ----------------
def retrieve_context(query):
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2
    )

    return "\n".join(results["documents"][0])