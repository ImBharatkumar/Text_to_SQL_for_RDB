import os
import json
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_index.json")
MODEL_NAME = "snowflake/snowflake-arctic-embed-m-v1.5"

class SchemaRetriever:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self.index = []  # List of dicts: {"domain": str, "table": str, "text": str, "embedding": List[float]}

    @property
    def model(self):
        if self._model is None:
            # Load model lazily
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def load_cache(self) -> bool:
        """Loads index cache if it exists."""
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r") as f:
                    self.index = json.load(f)
                return True
            except Exception as e:
                print(f"Error loading cache: {e}")
        return False

    def save_cache(self) -> None:
        """Saves index cache to disk."""
        with open(CACHE_PATH, "w") as f:
            json.dump(self.index, f)

    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """
        Builds the vector index from serialized document dicts:
        [{"domain": "...", "table": "...", "text": "..."}]
        """
        texts = [doc["text"] for doc in documents]
        if not texts:
            self.index = []
            self.save_cache()
            return

        # Arctic-embed documents don't need prefix, but query does.
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        
        self.index = []
        for doc, emb in zip(documents, embeddings):
            self.index.append({
                "domain": doc["domain"],
                "table": doc["table"],
                "text": doc["text"],
                "embedding": emb.tolist()
            })
        self.save_cache()

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top_k matches based on cosine similarity.
        Query for snowflake-arctic-embed should be prefixed with instruction.
        """
        if not self.index:
            self.load_cache()
            if not self.index:
                return []

        # Prefix for queries in Snowflake Arctic embed
        query_text = f"Represent this query for retrieval: {query}"
        query_emb = self.model.encode(query_text, normalize_embeddings=True)

        results = []
        for entry in self.index:
            emb = np.array(entry["embedding"])
            # since embeddings are normalized, dot product is cosine similarity
            similarity = float(np.dot(query_emb, emb))
            results.append({
                "domain": entry["domain"],
                "table": entry["table"],
                "text": entry["text"],
                "similarity": similarity
            })

        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
