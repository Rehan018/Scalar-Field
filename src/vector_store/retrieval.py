from typing import List, Dict, Optional, Set
import re
from datetime import datetime

from .vector_db import VectorDB


class RetrievalEngine:
    def __init__(self):
        self.vector_db = VectorDB()
    
    def search_with_filters(self, query: str, ticker: Optional[str] = None,
                          filing_type: Optional[str] = None,
                          date_range: Optional[tuple] = None,
                          n_results: int = 10) -> List[Dict]:
        """Search with multiple filters."""
        
        filters = {}
        
        if ticker:
            filters["ticker"] = ticker.upper()
        
        if filing_type:
            filters["filing_type"] = filing_type
        
        if date_range:
            # ChromaDB doesn't support date range queries directly
            # We'll filter after retrieval
            pass
        
        # Get results from vector database
        results = self.vector_db.search(query, n_results=n_results*2, filters=filters)
        
        # Apply date filtering if specified
        if date_range:
            results = self._filter_by_date_range(results, date_range)
        
        # Limit to requested number of results
        return results[:n_results]
    
    def search_multi_ticker(self, query: str, tickers: List[str],
                           n_results: int = 10) -> Dict[str, List[Dict]]:
        """Search across multiple tickers."""
        
        results = {}
        
        for ticker in tickers:
            ticker_results = self.search_with_filters(
                query, ticker=ticker, n_results=n_results//len(tickers) + 1
            )
            results[ticker] = ticker_results
        
        return results
    
    def search_by_section(self, query: str, section_keywords: List[str],
                         n_results: int = 10) -> List[Dict]:
        """Search within specific document sections."""
        
        # Enhance query with section keywords
        enhanced_query = f"{query} {' '.join(section_keywords)}"
        
        results = self.vector_db.search(enhanced_query, n_results=n_results)
        
        # Filter results that likely contain the section
        filtered_results = []
        for result in results:
            text_lower = result["text"].lower()
            if any(keyword.lower() in text_lower for keyword in section_keywords):
                filtered_results.append(result)
        
        return filtered_results[:n_results]
    
    def search_temporal(self, query: str, year: Optional[int] = None,
                       quarter: Optional[str] = None) -> List[Dict]:
        """Search with temporal constraints."""
        
        filters = {}
        
        if year:
            # Filter by year in filing_date
            # This is a simplified approach
            pass
        
        results = self.vector_db.search(query, n_results=20, filters=filters)
        
        # Post-process for temporal filtering
        if year or quarter:
            results = self._filter_by_temporal_criteria(results, year, quarter)
        
        return results
    
    def hybrid_search(self, query: str, keyword_boost: float = 0.3,
                     n_results: int = 10) -> List[Dict]:
        """Combine semantic and keyword search."""
        
        # Get semantic search results
        semantic_results = self.vector_db.search(query, n_results=n_results*2)
        
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        # Re-rank results based on keyword presence
        for result in semantic_results:
            keyword_score = self._calculate_keyword_score(result["text"], keywords)
            
            # Combine semantic similarity with keyword score
            combined_score = (
                result["similarity"] * (1 - keyword_boost) + 
                keyword_score * keyword_boost
            )
            result["combined_score"] = combined_score
        
        # Sort by combined score
        semantic_results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return semantic_results[:n_results]
    
    def _filter_by_date_range(self, results: List[Dict], 
                             date_range: tuple) -> List[Dict]:
        """Filter results by date range."""
        
        start_date, end_date = date_range
        filtered_results = []
        
        for result in results:
            filing_date = result["metadata"].get("filing_date", "")
            if filing_date and start_date <= filing_date <= end_date:
                filtered_results.append(result)
        
        return filtered_results
    
    def _filter_by_temporal_criteria(self, results: List[Dict], 
                                   year: Optional[int],
                                   quarter: Optional[str]) -> List[Dict]:
        """Filter results by year and quarter."""
        
        filtered_results = []
        
        for result in results:
            filing_date = result["metadata"].get("filing_date", "")
            
            if year and filing_date:
                if not filing_date.startswith(str(year)):
                    continue
            
            if quarter and result["metadata"].get("filing_type") == "10-Q":
                # Simple quarter detection logic
                if quarter.upper() not in result["text"].upper():
                    continue
            
            filtered_results.append(result)
        
        return filtered_results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query."""
        
        # Remove common stop words and extract meaningful terms
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", 
            "for", "of", "with", "by", "what", "how", "when", "where", "why"
        }
        
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate keyword match score for text."""
        
        if not keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        
        return matches / len(keywords)
    
    def get_similar_chunks(self, chunk_id: str, n_results: int = 5) -> List[Dict]:
        """Find chunks similar to a given chunk."""
        
        # Get the original chunk
        try:
            original_results = self.vector_db.collection.get(ids=[chunk_id])
            if not original_results["documents"]:
                return []
            
            original_text = original_results["documents"][0]
            
            # Search for similar chunks
            similar_results = self.vector_db.search(original_text, n_results=n_results+1)
            
            # Remove the original chunk from results
            filtered_results = [
                result for result in similar_results 
                if result["metadata"].get("chunk_id") != chunk_id
            ]
            
            return filtered_results[:n_results]
            
        except Exception as e:
            print(f"Error finding similar chunks: {e}")
            return []