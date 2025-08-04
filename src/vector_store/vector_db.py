from typing import List, Dict, Optional
import json
import os
import numpy as np
import pickle
from datetime import datetime

from .embeddings import EmbeddingGenerator
from document_processing.document_chunker import DocumentChunk
from config.settings import CHROMA_PERSIST_DIRECTORY


class VectorDB:
    def __init__(self, collection_name: str = "sec_filings"):
        self.embedding_generator = EmbeddingGenerator()
        self.collection_name = collection_name
        self.chunks_data = []
        self.embeddings_data = []
        self.metadata_index = {}
        
        os.makedirs(CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        self.storage_path = os.path.join(CHROMA_PERSIST_DIRECTORY, f"{collection_name}.pkl")
        self._load_from_disk()
        print("[INFO] Enhanced vector storage initialized")
    
    def add_chunks(self, chunks: List[DocumentChunk]):
        
        if not chunks:
            print("No chunks to add")
            return
        
        print(f"Adding {len(chunks)} chunks to vector database...")
        
        texts = [chunk.content for chunk in chunks]
        print("Generating embeddings...")
        embeddings = self.embedding_generator.generate_embeddings(texts)
        
        for i, chunk in enumerate(chunks):
            chunk_data = {
                'text': chunk.content,
                'metadata': chunk.metadata,
                'chunk_id': chunk.chunk_id,
                'embedding': embeddings[i] if len(embeddings) > i else None,
                'added_date': datetime.now().isoformat()
            }
            
            self.chunks_data.append(chunk_data)
            
            self._update_metadata_index(chunk.metadata, len(self.chunks_data) - 1)
        
        self._save_to_disk()
        print(f"[OK] Successfully added {len(chunks)} chunks to vector database")
    
    def search(self, query: str, n_results: int = 10, 
               filters: Optional[Dict] = None) -> List[Dict]:
        
        if not self.chunks_data:
            return []
        
        candidate_indices = self._apply_filters(filters) if filters else list(range(len(self.chunks_data)))
        
        if not candidate_indices:
            return []
        
        query_embedding = self.embedding_generator.generate_single_embedding(query)
        
        results = []
        query_words = self._extract_meaningful_words(query)
        
        for idx in candidate_indices:
            chunk = self.chunks_data[idx]
            
            semantic_score = 0.0
            if chunk.get('embedding') is not None:
                raw_semantic_score = self._cosine_similarity(query_embedding, chunk['embedding'])
                semantic_score = max(0.0, raw_semantic_score)
            
            keyword_score = self._calculate_enhanced_keyword_score(chunk['text'], query_words)
            
            if self.embedding_generator.use_fallback:
                combined_score = 0.4 * semantic_score + 0.6 * keyword_score
                min_threshold = 0.05
            else:
                combined_score = 0.7 * semantic_score + 0.3 * keyword_score
                min_threshold = 0.1
            
            if combined_score > min_threshold:
                results.append({
                    "text": chunk['text'],
                    "metadata": chunk['metadata'],
                    "chunk_id": chunk['chunk_id'],
                    "similarity": combined_score,
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:n_results]
    
    def get_collection_stats(self) -> Dict:
        
        if not self.chunks_data:
            return {"total_chunks": 0}
        
        tickers = set()
        filing_types = set()
        sectors = set()
        dates = []
        word_counts = []
        
        for chunk in self.chunks_data:
            metadata = chunk['metadata']
            
            if "ticker" in metadata:
                tickers.add(metadata["ticker"])
            if "filing_type" in metadata:
                filing_types.add(metadata["filing_type"])
            if "sector" in metadata:
                sectors.add(metadata["sector"])
            if "filing_date" in metadata:
                dates.append(metadata["filing_date"])
            if "chunk_word_count" in metadata:
                word_counts.append(metadata["chunk_word_count"])
        
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
        total_words = sum(word_counts) if word_counts else 0
        
        return {
            "total_chunks": len(self.chunks_data),
            "unique_tickers": len(tickers),
            "unique_filing_types": len(filing_types),
            "unique_sectors": len(sectors),
            "tickers": sorted(list(tickers)),
            "filing_types": sorted(list(filing_types)),
            "sectors": sorted(list(sectors)),
            "date_range": {
                "earliest": min(dates) if dates else None,
                "latest": max(dates) if dates else None
            },
            "word_statistics": {
                "total_words": total_words,
                "average_words_per_chunk": avg_word_count,
                "min_words": min(word_counts) if word_counts else 0,
                "max_words": max(word_counts) if word_counts else 0
            },
            "embeddings_available": sum(1 for chunk in self.chunks_data if chunk.get('embedding') is not None)
        }
    
    def search_by_metadata(self, metadata_filters: Dict, n_results: int = 10) -> List[Dict]:
        
        candidate_indices = self._apply_filters(metadata_filters)
        results = []
        
        for idx in candidate_indices[:n_results]:
            chunk = self.chunks_data[idx]
            results.append({
                "text": chunk['text'],
                "metadata": chunk['metadata'],
                "chunk_id": chunk['chunk_id'],
                "similarity": 1.0
            })
        
        return results
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        
        for chunk in self.chunks_data:
            if chunk['chunk_id'] == chunk_id:
                return {
                    "text": chunk['text'],
                    "metadata": chunk['metadata'],
                    "chunk_id": chunk['chunk_id']
                }
        return None
    
    def get_similar_chunks(self, chunk_id: str, n_results: int = 5) -> List[Dict]:
        
        target_chunk = None
        for chunk in self.chunks_data:
            if chunk['chunk_id'] == chunk_id:
                target_chunk = chunk
                break
        
        if not target_chunk or not target_chunk.get('embedding'):
            return []
        
        results = []
        target_embedding = target_chunk['embedding']
        
        for chunk in self.chunks_data:
            if chunk['chunk_id'] != chunk_id and chunk.get('embedding') is not None:
                similarity = self._cosine_similarity(target_embedding, chunk['embedding'])
                
                results.append({
                    "text": chunk['text'],
                    "metadata": chunk['metadata'],
                    "chunk_id": chunk['chunk_id'],
                    "similarity": similarity
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:n_results]
    
    def _apply_filters(self, filters: Dict) -> List[int]:
        
        if not filters:
            return list(range(len(self.chunks_data)))
        
        matching_indices = []
        
        for idx, chunk in enumerate(self.chunks_data):
            metadata = chunk['metadata']
            match = True
            
            for key, value in filters.items():
                if key not in metadata:
                    match = False
                    break
                
                if isinstance(value, list):
                    if metadata[key] not in value:
                        match = False
                        break
                else:
                    if metadata[key] != value:
                        match = False
                        break
            
            if match:
                matching_indices.append(idx)
        
        return matching_indices
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    def _update_metadata_index(self, metadata: Dict, chunk_index: int):
        
        for key, value in metadata.items():
            if isinstance(value, (dict, list)):
                continue
                
            if not isinstance(value, (str, int, float, bool, type(None))):
                value = str(value)
            
            if key not in self.metadata_index:
                self.metadata_index[key] = {}
            
            if value not in self.metadata_index[key]:
                self.metadata_index[key][value] = []
            
            self.metadata_index[key][value].append(chunk_index)
    
    def _save_to_disk(self):
        
        try:
            data = {
                'chunks_data': self.chunks_data,
                'metadata_index': self.metadata_index,
                'collection_name': self.collection_name,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            print(f"[WARNING] Failed to save to disk: {e}")
    
    def _load_from_disk(self):
        
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'rb') as f:
                    data = pickle.load(f)
                
                self.chunks_data = data.get('chunks_data', [])
                self.metadata_index = data.get('metadata_index', {})
                
                if self.chunks_data:
                    print(f"[INFO] Loaded {len(self.chunks_data)} chunks from disk")
                    
                    if hasattr(self.embedding_generator, 'use_fallback') and self.embedding_generator.use_fallback:
                        self._fit_tfidf_on_loaded_data()
                    
        except Exception as e:
            print(f"[WARNING] Failed to load from disk: {e}")
            self.chunks_data = []
            self.metadata_index = {}
    
    def _fit_tfidf_on_loaded_data(self):
        
        try:
            if not self.chunks_data:
                return
            
            print("[INFO] Fitting TF-IDF on loaded document corpus...")
            
            texts = [chunk['text'] for chunk in self.chunks_data]
            
            batch_size = 500
            if len(texts) <= batch_size:
                self.embedding_generator.generate_embeddings(texts)
            else:
                print(f"[INFO] Processing {len(texts)} texts in batches of {batch_size}")
                self.embedding_generator.generate_embeddings(texts[:batch_size])
            
            print("[INFO] TF-IDF system fitted on document corpus")
            
        except Exception as e:
            print(f"[WARNING] Failed to fit TF-IDF on loaded data: {e}")
    
    def delete_collection(self):
        
        self.chunks_data = []
        self.metadata_index = {}
        
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        
        print(f"Deleted collection: {self.collection_name}")
    
    def reset_collection(self):
        
        self.chunks_data = []
        self.metadata_index = {}
        print(f"Reset collection: {self.collection_name}")
    
    def _extract_meaningful_words(self, query: str) -> List[str]:
        
        import re
        
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", 
            "for", "of", "with", "by", "what", "how", "when", "where", "why",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had"
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        return meaningful_words
    
    def _calculate_enhanced_keyword_score(self, text: str, query_words: List[str]) -> float:
        
        if not query_words:
            return 0.0
        
        text_lower = text.lower()
        
        exact_matches = sum(1 for word in query_words if f" {word} " in f" {text_lower} ")
        
        partial_matches = sum(1 for word in query_words if word in text_lower and f" {word} " not in f" {text_lower} ")
        
        total_score = (exact_matches * 1.0 + partial_matches * 0.5) / len(query_words)
        
        return min(1.0, total_score)