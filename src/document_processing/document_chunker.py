from typing import List, Dict, Optional
import re
from dataclasses import dataclass
import os

try:
    from .html_parser import HTMLParser
    from .filing_processors import FilingProcessorFactory
    from config.settings import CHUNK_SIZE, CHUNK_OVERLAP
except ImportError:
    from document_processing.html_parser import HTMLParser
    from document_processing.filing_processors import FilingProcessorFactory
    from src.config.settings import CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class DocumentChunk:
    content: str  # Changed from 'text' to 'content' for consistency
    metadata: Dict
    chunk_id: str = ""
    start_position: int = 0
    end_position: int = 0


class DocumentChunker:
    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.parser = HTMLParser()
        self.financial_identifier = FilingProcessorFactory.get_financial_content_identifier()
    
    def chunk_file(self, filepath: str) -> List[DocumentChunk]:
        """Process and chunk a single SEC filing."""
        
        # Extract metadata from filename
        filename = os.path.basename(filepath)
        file_metadata = self._extract_file_metadata(filename)
        
        # Parse the HTML file
        parsed_doc = self.parser.parse_file(filepath)
        
        if "error" in parsed_doc:
            print(f"Error parsing {filepath}: {parsed_doc['error']}")
            return []
        
        # Create base metadata
        base_metadata = {
            **file_metadata,
            "source_file": filepath,
            "document_info": parsed_doc.get("document_info", {}),
            "total_word_count": parsed_doc.get("word_count", 0)
        }
        
        # Chunk the document
        chunks = self._create_chunks(parsed_doc["full_text"], base_metadata)
        
        print(f"Created {len(chunks)} chunks from {filename}")
        return chunks
    
    def _extract_file_metadata(self, filename: str) -> Dict:
        """Extract metadata from SEC filing filename."""
        
        # Expected format: TICKER_FILINGTYPE_DATE.html
        parts = filename.replace('.html', '').split('_')
        
        metadata = {}
        
        if len(parts) >= 3:
            metadata['ticker'] = parts[0]
            metadata['filing_type'] = parts[1]
            metadata['filing_date'] = parts[2]
        
        return metadata

    def _is_index_page(self, text: str) -> bool:
        """Check if the text appears to be an SEC index page rather than actual filing content."""

        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()

        # Common indicators of SEC index pages
        index_indicators = [
            'filing detail',
            'edgar filing documents',
            'sec.gov',
            'latest filings',
            'filings search tools',
            'this page uses javascript',
            'edgar-logo'
        ]

        # Count how many indicators are present
        indicator_count = sum(1 for indicator in index_indicators if indicator in text_lower)

        # If we have multiple indicators and the text is short, it's likely an index page
        if indicator_count >= 3 and len(text.split()) < 1000:
            return True

        # Check for specific SEC index page patterns
        if 'filing detail' in text_lower and 'edgar' in text_lower and len(text.split()) < 500:
            return True

        return False

    def _create_chunks(self, text: str, base_metadata: Dict) -> List[DocumentChunk]:
        """Split text into overlapping chunks with comprehensive validation."""

        if not text or len(text.strip()) == 0:
            return []

        # Comprehensive content validation pipeline
        validation_result = self._validate_filing_content(text, base_metadata)
        
        if not validation_result['is_valid']:
            print(f"Skipping invalid content: {validation_result['reason']} - {base_metadata.get('source_file', 'unknown')}")
            return []

        # Split into words for more precise chunking
        words = text.split()

        # Additional quality check after word splitting
        if len(words) < 100:
            print(f"Skipping short document ({len(words)} words): {base_metadata.get('source_file', 'unknown')}")
            return []

        chunks = []
        start_idx = 0
        chunk_counter = 0

        while start_idx < len(words):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(words))

            # Extract chunk text
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)

            # Skip very short chunks
            if len(chunk_text.strip()) < 50:
                break
            
            # Enhanced metadata extraction and enrichment
            enhanced_metadata = self._enrich_chunk_metadata(
                chunk_text, base_metadata, chunk_counter, start_idx, end_idx, len(chunk_words)
            )
            
            # Generate unique chunk ID
            chunk_id = self._generate_chunk_id(base_metadata, chunk_counter)
            
            # Create chunk object
            chunk = DocumentChunk(
                content=chunk_text,  # Changed from 'text' to 'content'
                metadata=enhanced_metadata,
                chunk_id=chunk_id,
                start_position=start_idx,
                end_position=end_idx
            )
            
            chunks.append(chunk)
            chunk_counter += 1
            
            # Move start position with overlap
            next_start = end_idx - self.overlap

            # Prevent infinite loop - ensure we always make progress
            if next_start <= start_idx:
                next_start = start_idx + max(1, self.chunk_size // 2)

            start_idx = next_start

            # Additional safety check
            if start_idx >= len(words):
                break
        
        return chunks
    
    def _generate_chunk_id(self, metadata: Dict, chunk_index: int) -> str:
        """Generate unique chunk identifier."""
        
        ticker = metadata.get('ticker', 'UNK')
        filing_type = metadata.get('filing_type', 'UNK')
        filing_date = metadata.get('filing_date', 'UNK')
        
        return f"{ticker}_{filing_type}_{filing_date}_{chunk_index:04d}"
    
    def chunk_multiple_files(self, filepaths: List[str]) -> List[DocumentChunk]:
        """Process and chunk multiple SEC filings."""

        all_chunks = []
        processed_count = 0
        skipped_count = 0
        error_count = 0

        print(f"Processing {len(filepaths)} files...")

        for i, filepath in enumerate(filepaths):
            try:
                # Progress indicator
                if i % 50 == 0:
                    print(f"Progress: {i}/{len(filepaths)} files processed")

                file_chunks = self.chunk_file(filepath)
                if file_chunks:
                    all_chunks.extend(file_chunks)
                    processed_count += 1
                else:
                    skipped_count += 1

            except KeyboardInterrupt:
                print(f"\nProcessing interrupted by user at file {i}/{len(filepaths)}")
                break
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                error_count += 1
                continue

        print(f"\nProcessing complete:")
        print(f"  - Successfully processed: {processed_count} files")
        print(f"  - Skipped (index pages/short): {skipped_count} files")
        print(f"  - Errors: {error_count} files")
        print(f"  - Total chunks created: {len(all_chunks)}")

        return all_chunks
    
    def get_chunks_by_ticker(self, chunks: List[DocumentChunk], ticker: str) -> List[DocumentChunk]:
        """Filter chunks by company ticker."""
        
        return [chunk for chunk in chunks if chunk.metadata.get('ticker') == ticker]
    
    def get_chunks_by_filing_type(self, chunks: List[DocumentChunk], filing_type: str) -> List[DocumentChunk]:
        """Filter chunks by filing type."""
        
        return [chunk for chunk in chunks if chunk.metadata.get('filing_type') == filing_type]
    
    def get_chunks_by_date_range(self, chunks: List[DocumentChunk], 
                                start_date: str, end_date: str) -> List[DocumentChunk]:
        """Filter chunks by filing date range."""
        
        filtered_chunks = []
        
        for chunk in chunks:
            filing_date = chunk.metadata.get('filing_date', '')
            if start_date <= filing_date <= end_date:
                filtered_chunks.append(chunk)
        
        return filtered_chunks
    
    def get_chunk_statistics(self, chunks: List[DocumentChunk]) -> Dict:
        """Generate statistics about the chunks."""
        
        if not chunks:
            return {"total_chunks": 0}
        
        # Basic stats
        total_chunks = len(chunks)
        total_words = sum(chunk.metadata.get('chunk_word_count', 0) for chunk in chunks)
        
        # Group by ticker
        ticker_stats = {}
        for chunk in chunks:
            ticker = chunk.metadata.get('ticker', 'Unknown')
            if ticker not in ticker_stats:
                ticker_stats[ticker] = 0
            ticker_stats[ticker] += 1
        
        # Group by filing type
        filing_type_stats = {}
        for chunk in chunks:
            filing_type = chunk.metadata.get('filing_type', 'Unknown')
            if filing_type not in filing_type_stats:
                filing_type_stats[filing_type] = 0
            filing_type_stats[filing_type] += 1
        
        return {
            "total_chunks": total_chunks,
            "total_words": total_words,
            "average_words_per_chunk": total_words / total_chunks if total_chunks > 0 else 0,
            "chunks_by_ticker": ticker_stats,
            "chunks_by_filing_type": filing_type_stats,
            "unique_tickers": len(ticker_stats),
            "unique_filing_types": len(filing_type_stats)
        }
    
    def _validate_filing_content(self, text: str, metadata: Dict) -> Dict:
        """Comprehensive content validation pipeline for SEC filings."""
        
        text_lower = text.lower()
        word_count = len(text.split())
        filing_type = metadata.get('filing_type', '')
        
        # Check 1: XBRL viewer page detection
        xbrl_indicators = [
            'xbrl viewer', 'ixviewer', 'loadviewer', 'javascript',
            'iframe', 'this page uses javascript', 'edgar-logo',
            'filing detail', 'edgar filing documents'
        ]
        
        xbrl_count = sum(1 for indicator in xbrl_indicators if indicator in text_lower)
        
        if xbrl_count >= 3 and word_count < 1000:
            return {
                'is_valid': False,
                'reason': 'XBRL viewer page detected',
                'quality_score': 0.0
            }
        
        # Check 2: Minimum content length
        if word_count < 100:
            return {
                'is_valid': False,
                'reason': f'Content too short ({word_count} words)',
                'quality_score': 0.1
            }
        
        # Check 3: Filing-specific content validation
        filing_content_score = self._calculate_filing_content_score(text_lower, filing_type)
        
        if filing_content_score < 0.3:
            return {
                'is_valid': False,
                'reason': f'Low filing content score ({filing_content_score:.2f})',
                'quality_score': filing_content_score
            }
        
        # Check 4: Financial content indicators
        financial_score = self._calculate_financial_content_score(text_lower)
        
        # Calculate overall quality score
        quality_score = (filing_content_score + financial_score) / 2
        
        return {
            'is_valid': True,
            'reason': 'Content validation passed',
            'quality_score': quality_score,
            'filing_content_score': filing_content_score,
            'financial_content_score': financial_score
        }
    
    def _calculate_filing_content_score(self, text_lower: str, filing_type: str) -> float:
        """Calculate score based on filing-specific content indicators."""
        
        filing_indicators = {
            '10-K': [
                'annual report', 'business overview', 'risk factors', 
                'management discussion', 'financial statements', 'consolidated statements',
                'item 1', 'item 2', 'item 3', 'part i', 'part ii'
            ],
            '10-Q': [
                'quarterly report', 'financial statements', 'condensed consolidated',
                'management discussion', 'item 1', 'item 2', 'part i', 'part ii'
            ],
            '8-K': [
                'current report', 'item 1', 'item 2', 'item 3', 'item 4',
                'item 5', 'item 7', 'item 8', 'item 9', 'signature'
            ],
            'DEF 14A': [
                'proxy statement', 'annual meeting', 'executive compensation',
                'board of directors', 'shareholder', 'voting', 'proposal'
            ],
            '3': ['initial statement', 'beneficial ownership', 'securities owned'],
            '4': ['statement of changes', 'securities acquired', 'securities disposed'],
            '5': ['annual statement', 'securities beneficially owned']
        }
        
        expected_indicators = filing_indicators.get(filing_type, ['sec filing', 'securities', 'company'])
        
        # Count how many indicators are present
        found_indicators = sum(1 for indicator in expected_indicators if indicator in text_lower)
        
        # Calculate score (0.0 to 1.0)
        if not expected_indicators:
            return 0.0
        
        score = min(found_indicators / len(expected_indicators), 1.0)
        
        return score
    
    def _calculate_financial_content_score(self, text_lower: str) -> float:
        """Calculate score based on financial content indicators."""
        
        financial_terms = [
            'revenue', 'income', 'profit', 'loss', 'earnings', 'cash flow',
            'assets', 'liabilities', 'equity', 'debt', 'investment',
            'financial', 'fiscal', 'quarter', 'annual', 'million', 'billion',
            'percent', 'percentage', 'growth', 'decline', 'increase', 'decrease'
        ]
        
        # Count financial terms (with some weighting for importance)
        financial_count = 0
        for term in financial_terms:
            if term in text_lower:
                # Weight more important terms higher
                if term in ['revenue', 'income', 'profit', 'earnings', 'cash flow']:
                    financial_count += 2
                else:
                    financial_count += 1
        
        # Normalize score (0.0 to 1.0)
        max_possible_score = len(financial_terms) * 1.5  # Account for weighted terms
        score = min(financial_count / max_possible_score, 1.0)
        
        return score
    
    def _enrich_chunk_metadata(self, chunk_text: str, base_metadata: Dict, 
                              chunk_index: int, start_idx: int, end_idx: int, 
                              word_count: int) -> Dict:
        """Enhanced metadata extraction and enrichment for document chunks."""
        
        filing_type = base_metadata.get('filing_type', '')
        
        # Start with base chunk metadata
        enriched_metadata = {
            **base_metadata,
            "chunk_index": chunk_index,
            "start_word_position": start_idx,
            "end_word_position": end_idx,
            "chunk_word_count": word_count
        }
        
        # Financial content type identification
        content_types = self.financial_identifier.identify_financial_content_type(chunk_text)
        enriched_metadata["financial_content_types"] = content_types
        
        # Primary content type (most likely type)
        if content_types:
            enriched_metadata["primary_content_type"] = content_types[0]
        else:
            enriched_metadata["primary_content_type"] = "general"
        
        # Financial metrics extraction
        financial_metrics = self.financial_identifier.extract_financial_metrics(chunk_text)
        enriched_metadata["financial_metrics"] = financial_metrics
        
        # Count total financial metrics found
        total_metrics = sum(len(metrics) for metrics in financial_metrics.values())
        enriched_metadata["financial_metrics_count"] = total_metrics
        
        # Content quality scoring
        quality_score = self.financial_identifier.calculate_content_quality_score(
            chunk_text, filing_type
        )
        enriched_metadata["content_quality_score"] = quality_score
        
        # Section type classification based on content
        section_type = self._classify_section_type(chunk_text, content_types, filing_type)
        enriched_metadata["section_type"] = section_type
        
        # Extract key financial concepts
        financial_concepts = self._extract_financial_concepts(chunk_text)
        enriched_metadata["financial_concepts"] = financial_concepts
        
        # Create comprehensive source attribution
        source_attribution = self._create_source_attribution(base_metadata, chunk_index)
        enriched_metadata["source_attribution"] = source_attribution
        
        # Add searchable keywords for better retrieval
        keywords = self._extract_keywords(chunk_text, content_types)
        enriched_metadata["keywords"] = keywords
        
        return enriched_metadata
    
    def _classify_section_type(self, text: str, content_types: List[str], filing_type: str) -> str:
        """Classify the section type based on content analysis."""
        
        # Priority-based classification
        if "executive_compensation" in content_types:
            return "compensation"
        elif "risk_factors" in content_types:
            return "risk"
        elif "management_discussion" in content_types:
            return "management_analysis"
        elif "financial_statements" in content_types:
            return "financial"
        elif "governance" in content_types:
            return "governance"
        elif "business_overview" in content_types:
            return "business"
        else:
            # Fallback classification based on filing type
            if filing_type == "DEF 14A":
                return "governance"
            elif filing_type in ["10-K", "10-Q"]:
                return "financial"
            elif filing_type == "8-K":
                return "events"
            else:
                return "general"
    
    def _extract_financial_concepts(self, text: str) -> List[str]:
        """Extract key financial concepts from text."""
        
        concepts = []
        text_lower = text.lower()
        
        # Financial concept patterns
        concept_patterns = {
            "revenue_growth": [r"revenue.*growth", r"sales.*growth", r"top.*line.*growth"],
            "profitability": [r"profit.*margin", r"operating.*margin", r"net.*income"],
            "liquidity": [r"cash.*flow", r"working.*capital", r"liquidity"],
            "debt": [r"debt.*ratio", r"leverage", r"borrowing"],
            "market_share": [r"market.*share", r"competitive.*position"],
            "innovation": [r"research.*development", r"r&d", r"innovation"],
            "risk_management": [r"risk.*management", r"hedging", r"insurance"],
            "acquisitions": [r"acquisition", r"merger", r"m&a"],
            "dividends": [r"dividend", r"share.*repurchase", r"buyback"],
            "guidance": [r"guidance", r"outlook", r"forecast"]
        }
        
        for concept, patterns in concept_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    concepts.append(concept)
                    break
        
        return concepts
    
    def _create_source_attribution(self, base_metadata: Dict, chunk_index: int) -> Dict:
        """Create comprehensive source attribution for the chunk."""
        
        return {
            "company_ticker": base_metadata.get('ticker', 'Unknown'),
            "company_name": self._get_company_name(base_metadata.get('ticker', '')),
            "filing_type": base_metadata.get('filing_type', 'Unknown'),
            "filing_date": base_metadata.get('filing_date', 'Unknown'),
            "source_file": base_metadata.get('source_file', 'Unknown'),
            "chunk_position": chunk_index,
            "citation_text": self._generate_citation_text(base_metadata, chunk_index),
            "document_url": self._generate_document_url(base_metadata),
            "extraction_timestamp": self._get_current_timestamp()
        }
    
    def _get_company_name(self, ticker: str) -> str:
        """Get company name from ticker (simplified mapping)."""
        
        company_names = {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation", 
            "GOOGL": "Alphabet Inc.",
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc.",
            "JPM": "JPMorgan Chase & Co.",
            "BAC": "Bank of America Corporation",
            "WFC": "Wells Fargo & Company",
            "JNJ": "Johnson & Johnson",
            "PFE": "Pfizer Inc.",
            "XOM": "Exxon Mobil Corporation",
            "CVX": "Chevron Corporation",
            "WMT": "Walmart Inc.",
            "GE": "General Electric Company",
            "CAT": "Caterpillar Inc.",
            "BA": "The Boeing Company"
        }
        
        return company_names.get(ticker, f"{ticker} Inc.")
    
    def _generate_citation_text(self, base_metadata: Dict, chunk_index: int) -> str:
        """Generate citation text for the chunk."""
        
        ticker = base_metadata.get('ticker', 'Unknown')
        filing_type = base_metadata.get('filing_type', 'Unknown')
        filing_date = base_metadata.get('filing_date', 'Unknown')
        company_name = self._get_company_name(ticker)
        
        # Format date for citation
        if len(filing_date) == 8:  # YYYYMMDD format
            formatted_date = f"{filing_date[:4]}-{filing_date[4:6]}-{filing_date[6:8]}"
        else:
            formatted_date = filing_date
        
        return f"{company_name} {filing_type} filing dated {formatted_date}, Section {chunk_index + 1}"
    
    def _generate_document_url(self, base_metadata: Dict) -> str:
        """Generate document URL for SEC filing (placeholder)."""
        
        # This would generate actual SEC EDGAR URLs in production
        ticker = base_metadata.get('ticker', 'unknown')
        filing_type = base_metadata.get('filing_type', 'unknown')
        filing_date = base_metadata.get('filing_date', 'unknown')
        
        return f"https://www.sec.gov/edgar/search/#{ticker}_{filing_type}_{filing_date}"
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for extraction metadata."""
        
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _extract_keywords(self, text: str, content_types: List[str]) -> List[str]:
        """Extract searchable keywords from chunk text."""
        
        keywords = []
        text_lower = text.lower()
        
        # Add content types as keywords
        keywords.extend(content_types)
        
        # Financial keywords
        financial_keywords = [
            "revenue", "income", "profit", "loss", "earnings", "cash flow",
            "assets", "liabilities", "equity", "debt", "investment", "growth",
            "margin", "ratio", "performance", "results", "operations"
        ]
        
        for keyword in financial_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        # Business keywords
        business_keywords = [
            "strategy", "market", "competition", "customer", "product", "service",
            "technology", "innovation", "acquisition", "merger", "expansion",
            "risk", "opportunity", "challenge", "outlook", "guidance"
        ]
        
        for keyword in business_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        # Remove duplicates and return
        return list(set(keywords))