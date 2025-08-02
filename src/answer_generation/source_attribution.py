from typing import List, Dict, Set
from datetime import datetime
import re


class SourceAttributor:
    def __init__(self):
        self.filing_type_names = {
            "10-K": "Annual Report",
            "10-Q": "Quarterly Report", 
            "8-K": "Current Report",
            "DEF 14A": "Proxy Statement",
            "3": "Initial Statement of Ownership",
            "4": "Statement of Changes in Ownership",
            "5": "Annual Statement of Ownership"
        }
    
    def generate_citations(self, relevant_docs: List[Dict]) -> List[Dict]:
        """Generate formatted citations for relevant documents."""
        
        citations = []
        seen_sources = set()
        
        for i, doc in enumerate(relevant_docs):
            metadata = doc.get("metadata", {})
            
            # Create unique source identifier
            source_key = (
                metadata.get("ticker", "Unknown"),
                metadata.get("filing_type", "Unknown"),
                metadata.get("filing_date", "Unknown")
            )
            
            # Skip duplicate sources
            if source_key in seen_sources:
                continue
            
            seen_sources.add(source_key)
            
            citation = self._format_citation(metadata, i + 1)
            citations.append(citation)
        
        return citations
    
    def _format_citation(self, metadata: Dict, citation_number: int) -> Dict:
        """Format a single citation."""
        
        ticker = metadata.get("ticker", "Unknown")
        filing_type = metadata.get("filing_type", "Unknown")
        filing_date = metadata.get("filing_date", "Unknown")
        company_name = metadata.get("company_name", ticker)
        
        # Get full filing type name
        filing_name = self.filing_type_names.get(filing_type, filing_type)
        
        # Format date
        formatted_date = self._format_date(filing_date)
        
        # Create citation text
        citation_text = f"{company_name} ({ticker}) - {filing_name} ({filing_type}), Filed: {formatted_date}"
        
        return {
            "citation_number": citation_number,
            "citation_text": citation_text,
            "ticker": ticker,
            "company_name": company_name,
            "filing_type": filing_type,
            "filing_date": filing_date,
            "formatted_date": formatted_date,
            "source_reliability": self._assess_source_reliability(metadata)
        }
    
    def _format_date(self, date_string: str) -> str:
        """Format date string for citation."""
        
        if not date_string or date_string == "Unknown":
            return "Date Unknown"
        
        # Handle different date formats
        try:
            # Try YYYYMMDD format
            if len(date_string) == 8 and date_string.isdigit():
                year = date_string[:4]
                month = date_string[4:6]
                day = date_string[6:8]
                return f"{month}/{day}/{year}"
            
            # Try YYYY-MM-DD format
            elif "-" in date_string:
                parts = date_string.split("-")
                if len(parts) == 3:
                    return f"{parts[1]}/{parts[2]}/{parts[0]}"
            
            return date_string
            
        except:
            return date_string
    
    def _assess_source_reliability(self, metadata: Dict) -> str:
        """Assess the reliability of the source."""
        
        filing_type = metadata.get("filing_type", "")
        filing_date = metadata.get("filing_date", "")
        
        # Primary sources (official SEC filings) are highly reliable
        if filing_type in ["10-K", "10-Q", "8-K", "DEF 14A"]:
            reliability = "High"
        elif filing_type in ["3", "4", "5"]:
            reliability = "Medium-High"
        else:
            reliability = "Medium"
        
        # Adjust based on recency
        if filing_date:
            try:
                if filing_date.startswith("2024") or filing_date.startswith("2023"):
                    pass  # Keep current reliability
                elif filing_date.startswith("2022"):
                    if reliability == "High":
                        reliability = "Medium-High"
                elif filing_date.startswith("2021") or filing_date.startswith("2020"):
                    if reliability == "High":
                        reliability = "Medium"
            except:
                pass
        
        return reliability
    
    def generate_source_summary(self, citations: List[Dict]) -> Dict:
        """Generate a summary of all sources used."""
        
        if not citations:
            return {"total_sources": 0}
        
        # Count by filing type
        filing_type_counts = {}
        company_counts = {}
        reliability_counts = {}
        
        for citation in citations:
            # Filing type counts
            filing_type = citation["filing_type"]
            filing_type_counts[filing_type] = filing_type_counts.get(filing_type, 0) + 1
            
            # Company counts
            ticker = citation["ticker"]
            company_counts[ticker] = company_counts.get(ticker, 0) + 1
            
            # Reliability counts
            reliability = citation["source_reliability"]
            reliability_counts[reliability] = reliability_counts.get(reliability, 0) + 1
        
        # Find date range
        dates = [c["filing_date"] for c in citations if c["filing_date"] != "Unknown"]
        date_range = None
        if dates:
            sorted_dates = sorted(dates)
            if len(sorted_dates) > 1:
                date_range = f"{self._format_date(sorted_dates[0])} to {self._format_date(sorted_dates[-1])}"
            else:
                date_range = self._format_date(sorted_dates[0])
        
        return {
            "total_sources": len(citations),
            "unique_companies": len(company_counts),
            "filing_type_breakdown": filing_type_counts,
            "company_breakdown": company_counts,
            "reliability_breakdown": reliability_counts,
            "date_range": date_range,
            "primary_sources": len([c for c in citations if c["source_reliability"] == "High"])
        }
    
    def format_inline_citations(self, answer: str, citations: List[Dict]) -> str:
        """Add inline citations to the answer text."""
        
        if not citations:
            return answer
        
        # Simple approach: add citation numbers at the end of sentences
        # that likely reference specific information
        
        # Patterns that suggest specific information
        citation_patterns = [
            r'according to[^.]*\.',
            r'reported[^.]*\.',
            r'disclosed[^.]*\.',
            r'stated[^.]*\.',
            r'filed[^.]*\.',
            r'\$[\d,]+[^.]*\.',
            r'\d+%[^.]*\.',
            r'in \d{4}[^.]*\.'
        ]
        
        modified_answer = answer
        citation_counter = 1
        
        for pattern in citation_patterns:
            matches = list(re.finditer(pattern, modified_answer, re.IGNORECASE))
            for match in reversed(matches):  # Reverse to maintain positions
                if citation_counter <= len(citations):
                    citation_text = f" [{citation_counter}]"
                    modified_answer = (
                        modified_answer[:match.end()-1] + 
                        citation_text + 
                        modified_answer[match.end()-1:]
                    )
                    citation_counter += 1
        
        return modified_answer
    
    def generate_bibliography(self, citations: List[Dict]) -> str:
        """Generate a formatted bibliography."""
        
        if not citations:
            return "No sources cited."
        
        bibliography = "Sources:\n"
        
        for citation in citations:
            bibliography += f"[{citation['citation_number']}] {citation['citation_text']}\n"
        
        return bibliography
    
    def validate_source_attribution(self, answer: str, relevant_docs: List[Dict]) -> Dict:
        """Validate that the answer properly attributes sources."""
        
        validation_results = {
            "has_attribution": False,
            "attribution_quality": "Poor",
            "missing_attributions": [],
            "recommendations": []
        }
        
        # Check for basic attribution indicators
        attribution_indicators = [
            "according to", "reported", "disclosed", "stated", "filed",
            "sec filing", "annual report", "quarterly report"
        ]
        
        has_indicators = any(indicator in answer.lower() 
                           for indicator in attribution_indicators)
        
        if has_indicators:
            validation_results["has_attribution"] = True
            validation_results["attribution_quality"] = "Good"
        
        # Check for specific company/filing references
        companies_mentioned = set()
        for doc in relevant_docs:
            ticker = doc.get("metadata", {}).get("ticker", "")
            if ticker and ticker.lower() in answer.lower():
                companies_mentioned.add(ticker)
        
        if companies_mentioned:
            validation_results["attribution_quality"] = "Very Good"
        
        # Generate recommendations
        if not has_indicators:
            validation_results["recommendations"].append(
                "Add source attribution phrases like 'according to SEC filings'"
            )
        
        if not companies_mentioned:
            validation_results["recommendations"].append(
                "Reference specific companies and filing types"
            )
        
        return validation_results