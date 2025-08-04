import numpy as np
from typing import List, Dict
import os
import hashlib
import re

from config.settings import EMBEDDINGS_DIR, EMBEDDING_MODEL


class EmbeddingGenerator:
    def __init__(self, model_name: str = None):
        if model_name is None:
            model_name = EMBEDDING_MODEL
        self.model_name = model_name
        self.model = None
        self.use_fallback = False
        
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            print(f"[INFO] Successfully loaded sentence-transformers model: {model_name}")
        except ImportError as e:
            print(f"[WARNING] sentence-transformers not available: {e}")
            print("[INFO] Using fallback TF-IDF based embeddings")
            self.use_fallback = True
            self._init_fallback_embeddings()
        except Exception as e:
            print(f"[WARNING] Error loading sentence-transformers: {e}")
            print("[INFO] Using fallback TF-IDF based embeddings")
            self.use_fallback = True
            self._init_fallback_embeddings()
    
    def _init_fallback_embeddings(self):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
            
            financial_stop_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            
            self.tfidf = TfidfVectorizer(
                max_features=5000,
                stop_words=financial_stop_words,
                ngram_range=(1, 2),
                min_df=1,
                max_df=1.0
            )
            
            self.svd = TruncatedSVD(n_components=384, random_state=42)
            self.is_fitted = False
            
        except ImportError:
            print("[ERROR] sklearn not available for fallback embeddings")
            raise ImportError("Neither sentence-transformers nor sklearn available for embeddings")
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        
        if not texts:
            return np.array([])
        
        if self.use_fallback:
            return self._generate_fallback_embeddings(texts)
        else:
            embeddings = self.model.encode(texts, show_progress_bar=True)
            return embeddings
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        
        if self.use_fallback:
            if not self.is_fitted:
                print("[WARNING] TF-IDF not fitted yet, attempting to fit on single text")
                try:
                    self._generate_fallback_embeddings([text])
                except Exception as e:
                    print(f"[ERROR] Failed to fit TF-IDF on single text: {e}")
                    return np.zeros(384, dtype=np.float32)
            
            cleaned_text = self._preprocess_financial_text(text)
            
            try:
                tfidf_matrix = self.tfidf.transform([cleaned_text])
                
                embedding = self.svd.transform(tfidf_matrix)
                
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                
                return embedding[0].astype(np.float32)
            except Exception as e:
                print(f"[ERROR] Failed to generate single embedding: {e}")
                return np.zeros(384, dtype=np.float32)
        else:
            return self.model.encode([text])[0]
    
    def get_embedding_dimension(self) -> int:
        
        if self.use_fallback:
            return 384
        else:
            return self.model.get_sentence_embedding_dimension()
    
    def _generate_fallback_embeddings(self, texts: List[str]) -> np.ndarray:
        
        cleaned_texts = [self._preprocess_financial_text(text) for text in texts]
        
        if not self.is_fitted:
            tfidf_matrix = self.tfidf.fit_transform(cleaned_texts)
            self.svd.fit(tfidf_matrix)
            self.is_fitted = True
        else:
            tfidf_matrix = self.tfidf.transform(cleaned_texts)
        
        embeddings = self.svd.transform(tfidf_matrix)
        
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings = embeddings / norms
        
        return embeddings.astype(np.float32)
    
    def _preprocess_financial_text(self, text: str) -> str:
        
        text = text.lower()
        
        text = re.sub(r'\s+', ' ', text)
        
        text = re.sub(r'[^\w\s\.\$\%\-]', ' ', text)
        
        words = text.split()
        important_short = {'r&d', 'ai', 'it', 'us', 'uk', 'eu', 'ceo', 'cfo', 'sec'}
        words = [word for word in words if len(word) >= 2 or word in important_short]
        
        return ' '.join(words)
    
    def save_embeddings(self, embeddings: np.ndarray, filename: str):
        
        os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
        filepath = os.path.join(EMBEDDINGS_DIR, filename)
        np.save(filepath, embeddings)
        print(f"Embeddings saved to {filepath}")
    
    def load_embeddings(self, filename: str) -> np.ndarray:
        
        filepath = os.path.join(EMBEDDINGS_DIR, filename)
        if os.path.exists(filepath):
            return np.load(filepath)
        else:
            raise FileNotFoundError(f"Embeddings file not found: {filepath}")