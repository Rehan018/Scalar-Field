from typing import List, Dict, Optional
import re
from dataclasses import dataclass
import os

try:
    from .html_parser import HTMLParser
    from config.settings import CHUNK_SIZE, CHUNK_OVERLAP
except ImportError:
    from document_processing.html_parser import HTMLParser
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
        """Split text into overlapping chunks."""

        if not text or len(text.strip()) == 0:
            return []

        # Check if this looks like an SEC index page rather than actual filing content
        if self._is_index_page(text):
            print(f"Skipping index page: {base_metadata.get('source_file', 'unknown')}")
            return []

        # Split into words for more precise chunking
        words = text.split()

        # Skip documents that are too short to be meaningful
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
            
            # Create chunk metadata
            chunk_metadata = {
                **base_metadata,
                "chunk_index": chunk_counter,
                "start_word_position": start_idx,
                "end_word_position": end_idx,
                "chunk_word_count": len(chunk_words)
            }
            
            # Generate unique chunk ID
            chunk_id = self._generate_chunk_id(base_metadata, chunk_counter)
            
            # Create chunk object
            chunk = DocumentChunk(
                content=chunk_text,  # Changed from 'text' to 'content'
                metadata=chunk_metadata,
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