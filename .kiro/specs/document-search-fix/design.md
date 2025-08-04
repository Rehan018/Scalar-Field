# Design Document

## Overview

The SEC filing analysis system is experiencing a critical issue where document search returns 0 relevant documents for user queries, preventing users from accessing the wealth of financial data stored in the system. Through analysis of the codebase and testing, several root causes have been identified that need to be addressed to restore proper search functionality.

The system currently has 1,209 document chunks loaded from 14 companies across various SEC filing types, but the search pipeline has multiple failure points that prevent users from accessing this data effectively.

## Architecture

The document search pipeline consists of several interconnected components:

```
User Query → Entity Extractor → Query Router → Retrieval Engine → Vector DB → Answer Synthesizer
```

### Current Architecture Issues

1. **Entity Extraction Layer**: Incorrectly identifies company tickers from substring matches
2. **Embedding Generation**: TF-IDF fallback system has initialization and fitting issues
3. **Similarity Scoring**: Threshold and scoring mechanisms not optimized for TF-IDF embeddings
4. **Query Classification**: Misroutes queries due to faulty entity extraction

## Components and Interfaces

### 1. Entity Extractor (`src/query_processing/entity_extractor.py`)

**Current Issues:**
- Substring matching causes false positives (e.g., "GE" detected in "financial services")
- No word boundary checking for ticker extraction
- Overly aggressive company name matching

**Required Changes:**
- Implement word boundary checking for ticker extraction
- Add context validation to prevent false matches
- Improve company name matching with better tokenization

### 2. Embedding Generator (`src/vector_store/embeddings.py`)

**Current Issues:**
- TF-IDF fallback system not properly fitted when generating single embeddings
- Inconsistent embedding dimensions between batch and single generation
- Poor handling of edge cases when TF-IDF is not fitted

**Required Changes:**
- Ensure TF-IDF system is always fitted before single embedding generation
- Implement consistent embedding normalization
- Add proper error handling for unfitted TF-IDF scenarios

### 3. Vector Database (`src/vector_store/vector_db.py`)

**Current Issues:**
- Similarity threshold (0.1) may be too restrictive for TF-IDF embeddings
- Combined scoring algorithm not optimized for TF-IDF semantic scores
- Inconsistent handling of zero embeddings

**Required Changes:**
- Adjust similarity thresholds for TF-IDF-based embeddings
- Improve combined scoring algorithm weighting
- Add validation for embedding quality before storage

### 4. Query Router (`src/query_processing/query_router.py`)

**Current Issues:**
- Relies on faulty entity extraction for query classification
- Misclassifies general queries as single-company queries
- Doesn't handle entity extraction errors gracefully

**Required Changes:**
- Add validation layer for entity extraction results
- Implement fallback query classification logic
- Improve handling of ambiguous queries

### 5. LLM Client (`src/answer_generation/llm_client.py`)

**Current Issues:**
- Gemini API rate limiting prevents answer generation
- System fails when LLM service is unavailable
- No fallback LLM options configured

**Required Changes:**
- Replace Gemini API with local Ollama models (http://10.10.110.25:11434/)
- Implement proper Ollama API integration
- Add error handling for local model connectivity

## Data Models

### Embedding Data Model
```python
{
    'text': str,                    # Original chunk text
    'metadata': dict,               # Filing metadata
    'chunk_id': str,               # Unique identifier
    'embedding': np.ndarray,       # Normalized embedding vector
    'embedding_method': str,       # 'sentence-transformers' or 'tfidf'
    'embedding_quality': float,    # Quality score (0-1)
    'added_date': str             # ISO timestamp
}
```

### Search Result Model
```python
{
    'text': str,                   # Chunk content
    'metadata': dict,              # Filing metadata
    'chunk_id': str,              # Unique identifier
    'similarity': float,           # Combined similarity score
    'semantic_score': float,       # Semantic similarity component
    'keyword_score': float,        # Keyword matching component
    'embedding_method': str        # Method used for embedding
}
```

## Error Handling

### 1. Entity Extraction Errors
- **False Positive Detection**: Validate ticker matches against context
- **Missing Entities**: Provide fallback to general search when no entities found
- **Ambiguous Matches**: Use confidence scoring for entity extraction

### 2. Embedding Generation Errors
- **TF-IDF Not Fitted**: Automatically fit on available corpus or return zero vector with warning
- **Empty Text Input**: Handle gracefully with appropriate default embeddings
- **Dimension Mismatch**: Ensure consistent embedding dimensions across all methods

### 3. Search Errors
- **No Results Above Threshold**: Implement adaptive thresholding based on embedding method
- **Empty Database**: Provide clear error messages and system status information
- **Malformed Queries**: Sanitize and preprocess queries before processing

## Testing Strategy

### 1. Unit Tests
- **Entity Extraction**: Test ticker detection with various query formats
- **Embedding Generation**: Verify TF-IDF fitting and single embedding generation
- **Vector Database**: Test search functionality with different similarity thresholds
- **Query Routing**: Validate query classification logic

### 2. Integration Tests
- **End-to-End Search**: Test complete search pipeline with known queries
- **Cross-Component**: Verify data flow between components
- **Error Scenarios**: Test system behavior under various error conditions

### 3. Performance Tests
- **Search Latency**: Measure response times for different query types
- **Embedding Generation**: Test batch vs single embedding performance
- **Memory Usage**: Monitor memory consumption during search operations

### 4. Validation Tests
- **Search Quality**: Compare search results against expected outcomes
- **Similarity Scoring**: Validate that similarity scores reflect actual relevance
- **Entity Extraction Accuracy**: Test against manually labeled query dataset

## Implementation Approach

### Phase 1: Core Fixes
1. Fix entity extraction substring matching issues
2. Resolve TF-IDF fitting problems in embedding generation
3. Adjust similarity thresholds for TF-IDF embeddings
4. Replace Gemini API with local Ollama models
5. Improve query routing logic

### Phase 2: Enhanced Functionality
1. Implement adaptive similarity thresholds
2. Add embedding quality validation
3. Enhance error handling and user feedback
4. Optimize search performance

### Phase 3: Validation and Testing
1. Comprehensive testing of all components
2. Performance optimization
3. User acceptance testing with various query types
4. Documentation and monitoring improvements

## Success Metrics

1. **Search Success Rate**: >95% of valid queries return relevant results
2. **Result Relevance**: Average similarity scores >0.4 for relevant results
3. **Entity Extraction Accuracy**: <5% false positive rate for ticker detection
4. **System Reliability**: <1% error rate for search operations
5. **Response Time**: <2 seconds for typical search queries

## Risk Mitigation

1. **Backward Compatibility**: Ensure changes don't break existing functionality
2. **Data Integrity**: Validate that existing embeddings remain usable
3. **Performance Impact**: Monitor for any performance degradation
4. **Fallback Mechanisms**: Maintain robust fallback options for all components