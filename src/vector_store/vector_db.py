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
        
        # Enhanced storage with persistence
        os.makedirs(CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        self.storage_path = os.path.join(CHROMA_PERSIST_DIRECTORY, f"{collection_name}.pkl")
        self._load_from_disk()
        print("[INFO] Enhanced vector storage initialized")
    
    def add_chunks(self, chunks: List[DocumentChunk]):
        """Add document chunks with embeddings and indexing."""
        
        if not chunks:
            print("No chunks to add")
            return
        
        print(f"Adding {len(chunks)} chunks to vector database...")
        
        # Generate embeddings for all chunks
        texts = [chunk.text for chunk in chunks]
        print("Generating embeddings...")
        embeddings = self.embedding_generator.generate_embeddings(texts)
        
        # Store chunks with embeddings and build indexes
        for i, chunk in enumerate(chunks):
            chunk_data = {
                'text': chunk.text,
                'metadata': chunk.metadata,
                'chunk_id': chunk.chunk_id,
                'embedding': embeddings[i] if len(embeddings) > i else None,
                'added_date': datetime.now().isoformat()
            }
            
            self.chunks_data.append(chunk_data)
            
            # Build metadata indexes for faster filtering
            self._update_metadata_index(chunk.metadata, len(self.chunks_data) - 1)
        
        # Save to disk
        self._save_to_disk()
        print(f"[OK] Successfully added {len(chunks)} chunks to vector database")
    
    def search(self, query: str, n_results: int = 10, 
               filters: Optional[Dict] = None) -> List[Dict]:
        """Enhanced search with semantic similarity and keyword matching."""
        
        if not self.chunks_data:
            return []
        
        # Get filtered chunk indices
        candidate_indices = self._apply_filters(filters) if filters else list(range(len(self.chunks_data)))
        
        if not candidate_indices:
            return []
        
        # Generate query embedding for semantic search
        query_embedding = self.embedding_generator.generate_single_embedding(query)
        
        # Calculate similarities
        results = []
        query_words = query.lower().split()
        
        for idx in candidate_indices:
            chunk = self.chunks_data[idx]
            
            # Semantic similarity (if embeddings available)
            semantic_score = 0.0
            if chunk.get('embedding') is not None:
                semantic_score = self._cosine_similarity(query_embedding, chunk['embedding'])
            
            # Keyword similarity
            text_lower = chunk['text'].lower()
            keyword_score = sum(1 for word in query_words if word in text_lower) / len(query_words)
            
            # Combined score (weighted)
            combined_score = 0.7 * semantic_score + 0.3 * keyword_score
            
            if combined_score > 0.1:  # Minimum threshold
                results.append({
                    "text": chunk['text'],
                    "metadata": chunk['metadata'],
                    "chunk_id": chunk['chunk_id'],
                    "similarity": combined_score,
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score
                })
        
        # Sort by combined similarity and return top results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:n_results]
    
    def get_collection_stats(self) -> Dict:
        """Get comprehensive statistics about the collection."""
        
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
        
        # Calculate additional stats
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
        """Search chunks by metadata only."""
        
        candidate_indices = self._apply_filters(metadata_filters)
        results = []
        
        for idx in candidate_indices[:n_results]:
            chunk = self.chunks_data[idx]
            results.append({
                "text": chunk['text'],
                "metadata": chunk['metadata'],
                "chunk_id": chunk['chunk_id'],
                "similarity": 1.0  # Perfect match for metadata search
            })
        
        return results
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """Get a specific chunk by its ID."""
        
        for chunk in self.chunks_data:
            if chunk['chunk_id'] == chunk_id:
                return {
                    "text": chunk['text'],
                    "metadata": chunk['metadata'],
                    "chunk_id": chunk['chunk_id']
                }
        return None
    
    def get_similar_chunks(self, chunk_id: str, n_results: int = 5) -> List[Dict]:
        """Find chunks similar to a given chunk."""
        
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
        """Apply metadata filters and return matching chunk indices."""
        
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
        """Calculate cosine similarity between two vectors."""
        
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
        """Update metadata indexes for faster filtering."""
        
        for key, value in metadata.items():
            if key not in self.metadata_index:
                self.metadata_index[key] = {}
            
            if value not in self.metadata_index[key]:
                self.metadata_index[key][value] = []
            
            self.metadata_index[key][value].append(chunk_index)
    
    def _save_to_disk(self):
        """Save collection to disk for persistence."""
        
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
        """Load collection from disk if exists."""
        
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'rb') as f:
                    data = pickle.load(f)
                
                self.chunks_data = data.get('chunks_data', [])
                self.metadata_index = data.get('metadata_index', {})
                
                if self.chunks_data:
                    print(f"[INFO] Loaded {len(self.chunks_data)} chunks from disk")
                    
        except Exception as e:
            print(f"[WARNING] Failed to load from disk: {e}")
            self.chunks_data = []
            self.metadata_index = {}
    
    def delete_collection(self):
        """Delete the entire collection."""
        
        self.chunks_data = []
        self.metadata_index = {}
        
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        
        print(f"Deleted collection: {self.collection_name}")
    
    def reset_collection(self):
        """Reset the collection (delete and recreate)."""
        
        self.chunks_data = []
        self.metadata_index = {}
        print(f"Reset collection: {self.collection_name}")