import re
from typing import List, Dict, Optional, Set
from datetime import datetime

from config.settings import COMPANIES


class EntityExtractor:
    def __init__(self):
        # Create ticker to company name mapping
        self.ticker_to_name = {ticker: info["name"] for ticker, info in COMPANIES.items()}
        self.name_to_ticker = {info["name"].lower(): ticker for ticker, info in COMPANIES.items()}
        
        # Common company name variations
        self.company_variations = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "jpmorgan": "JPM",
            "jp morgan": "JPM",
            "bank of america": "BAC",
            "wells fargo": "WFC",
            "johnson & johnson": "JNJ",
            "johnson and johnson": "JNJ",
            "pfizer": "PFE",
            "exxon": "XOM",
            "exxon mobil": "XOM",
            "chevron": "CVX",
            "walmart": "WMT",
            "general electric": "GE",
            "caterpillar": "CAT",
            "boeing": "BA"
        }
    
    def extract_tickers(self, query: str) -> List[str]:
        """Extract company tickers from query."""
        
        tickers = set()
        query_lower = query.lower()
        
        # Direct ticker matches
        for ticker in COMPANIES.keys():
            if ticker.lower() in query_lower:
                tickers.add(ticker)
        
        # Company name matches
        for name_variant, ticker in self.company_variations.items():
            if name_variant in query_lower:
                tickers.add(ticker)
        
        # Full company name matches
        for full_name, ticker in self.name_to_ticker.items():
            if full_name in query_lower:
                tickers.add(ticker)
        
        return list(tickers)
    
    def extract_time_periods(self, query: str) -> Dict:
        """Extract time periods and dates from query."""
        
        time_info = {
            "years": [],
            "quarters": [],
            "specific_dates": [],
            "relative_terms": []
        }
        
        # Extract years (2020-2024)
        year_pattern = r'\b(20[2-4][0-9])\b'
        years = re.findall(year_pattern, query)
        time_info["years"] = list(set(years))
        
        # Extract quarters
        quarter_patterns = [
            r'\bQ[1-4]\b',
            r'\b[1-4]Q\b',
            r'\bfirst quarter\b',
            r'\bsecond quarter\b',
            r'\bthird quarter\b',
            r'\bfourth quarter\b'
        ]
        
        for pattern in quarter_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            time_info["quarters"].extend(matches)
        
        # Extract relative time terms
        relative_terms = [
            "recent", "latest", "current", "last year", "this year",
            "over time", "historical", "trend", "evolution"
        ]
        
        for term in relative_terms:
            if term in query.lower():
                time_info["relative_terms"].append(term)
        
        return time_info
    
    def extract_filing_types(self, query: str) -> List[str]:
        """Extract SEC filing types from query."""
        
        filing_types = []
        query_lower = query.lower()
        
        # Direct filing type matches
        filing_patterns = {
            r'\b10-k\b': '10-K',
            r'\bannual report\b': '10-K',
            r'\b10-q\b': '10-Q',
            r'\bquarterly report\b': '10-Q',
            r'\b8-k\b': '8-K',
            r'\bcurrent report\b': '8-K',
            r'\bproxy\b': 'DEF 14A',
            r'\bdef 14a\b': 'DEF 14A',
            r'\binsider trading\b': ['3', '4', '5'],
            r'\bform [345]\b': ['3', '4', '5']
        }
        
        for pattern, filing_type in filing_patterns.items():
            if re.search(pattern, query_lower):
                if isinstance(filing_type, list):
                    filing_types.extend(filing_type)
                else:
                    filing_types.append(filing_type)
        
        return list(set(filing_types))
    
    def extract_financial_concepts(self, query: str) -> List[str]:
        """Extract financial concepts and topics."""
        
        concepts = []
        query_lower = query.lower()
        
        financial_terms = {
            "revenue": ["revenue", "sales", "income", "earnings"],
            "expenses": ["expenses", "costs", "spending"],
            "profit": ["profit", "net income", "earnings"],
            "cash_flow": ["cash flow", "operating cash", "free cash flow"],
            "debt": ["debt", "liabilities", "borrowing"],
            "assets": ["assets", "balance sheet"],
            "risk_factors": ["risk", "risks", "risk factors"],
            "competition": ["competition", "competitive", "competitors"],
            "r&d": ["r&d", "research", "development", "innovation"],
            "acquisitions": ["acquisition", "merger", "m&a"],
            "executive_compensation": ["compensation", "executive pay", "salary"],
            "working_capital": ["working capital", "current assets"],
            "climate": ["climate", "environmental", "sustainability"],
            "ai_automation": ["ai", "artificial intelligence", "automation", "technology"]
        }
        
        for concept, keywords in financial_terms.items():
            if any(keyword in query_lower for keyword in keywords):
                concepts.append(concept)
        
        return concepts
    
    def extract_comparison_intent(self, query: str) -> Dict:
        """Detect if query involves comparison between entities."""
        
        comparison_info = {
            "is_comparison": False,
            "comparison_type": None,
            "entities": []
        }
        
        # Comparison keywords
        comparison_keywords = [
            "compare", "comparison", "versus", "vs", "against",
            "difference", "similar", "contrast", "between"
        ]
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in comparison_keywords):
            comparison_info["is_comparison"] = True
            
            # Determine comparison type
            if "trend" in query_lower or "over time" in query_lower:
                comparison_info["comparison_type"] = "temporal"
            elif len(self.extract_tickers(query)) > 1:
                comparison_info["comparison_type"] = "cross_company"
            else:
                comparison_info["comparison_type"] = "general"
            
            comparison_info["entities"] = self.extract_tickers(query)
        
        return comparison_info
    
    def extract_all_entities(self, query: str) -> Dict:
        """Extract all entities from query in one pass."""
        
        return {
            "tickers": self.extract_tickers(query),
            "time_periods": self.extract_time_periods(query),
            "filing_types": self.extract_filing_types(query),
            "financial_concepts": self.extract_financial_concepts(query),
            "comparison_intent": self.extract_comparison_intent(query),
            "original_query": query
        }