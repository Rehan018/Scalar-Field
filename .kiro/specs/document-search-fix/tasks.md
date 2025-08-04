# Implementation Plan

- [x] 1. Fix entity extraction substring matching issues
  - Implement word boundary checking for ticker detection to prevent false positives like "GE" from "financial services"
  - Add context validation to ensure ticker matches are legitimate company references
  - Update ticker extraction regex patterns to use word boundaries
  - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.3_

- [x] 2. Resolve TF-IDF embedding generation consistency issues
  - Fix TF-IDF fitting problem when generating single embeddings for queries
  - Ensure consistent embedding dimensions between batch and single generation methods
  - Add proper validation to check if TF-IDF is fitted before generating single embeddings
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3_

- [x] 3. Adjust similarity thresholds and scoring for TF-IDF embeddings
  - Lower the minimum similarity threshold from 0.1 to accommodate TF-IDF-based embeddings
  - Optimize the combined scoring algorithm weighting between semantic and keyword scores
  - Implement adaptive thresholding based on embedding method used
  - _Requirements: 1.1, 1.2, 5.1, 5.2, 5.3_

- [x] 4. Replace Gemini API with local Ollama models
  - Update LLM client to use local Ollama API endpoint (http://10.10.110.25:11434/)
  - Implement proper Ollama API integration with error handling
  - Add fallback mechanisms for when local models are unavailable
  - Test answer generation with local models to ensure quality
  - _Requirements: 4.1, 4.2, 4.3, 5.4_

- [ ] 5. Improve query routing and classification logic
  - Add validation layer for entity extraction results to catch false positives
  - Implement fallback to general search when entity extraction produces questionable results
  - Update query type determination logic to handle edge cases better
  - _Requirements: 3.1, 3.2, 3.3, 4.3_

- [ ] 6. Add comprehensive error handling and system diagnostics
  - Implement better error messages when vector database is empty or search fails
  - Add system status checks to validate embedding quality and database state
  - Create diagnostic tools to help identify search pipeline issues
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 7. Create comprehensive tests for search functionality
  - Write unit tests for entity extraction with various query formats
  - Create integration tests for end-to-end search pipeline
  - Add test cases for TF-IDF embedding generation and similarity scoring
  - Test query routing with different types of queries
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 5.1, 5.2, 5.3_

- [ ] 8. Validate and optimize search performance
  - Test search functionality with known good queries to ensure results are returned
  - Measure and optimize search response times
  - Validate that similarity scores reflect actual document relevance
  - Ensure system can handle various query types (financial metrics, risk factors, comparative analysis)
  - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.3, 4.4, 5.1, 5.2, 5.3, 5.4_