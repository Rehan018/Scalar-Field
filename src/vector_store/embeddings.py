from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import os

from config.settings import EMBEDDINGS_DIR


class EmbeddingGenerator:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        
        if not texts:
            return np.array([])
        
        # Generate embeddings
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        
        return self.model.encode([text])[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        
        return self.model.get_sentence_embedding_dimension()
    
    def save_embeddings(self, embeddings: np.ndarray, filename: str):
        """Save embeddings to file."""
        
        os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
        filepath = os.path.join(EMBEDDINGS_DIR, filename)
        np.save(filepath, embeddings)
        print(f"Embeddings saved to {filepath}")
    
    def load_embeddings(self, filename: str) -> np.ndarray:
        """Load embeddings from file."""
        
        filepath = os.path.join(EMBEDDINGS_DIR, filename)
        if os.path.exists(filepath):
            return np.load(filepath)
        else:
            raise FileNotFoundError(f"Embeddings file not found: {filepath}")