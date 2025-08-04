"""
Filing-specific document processors for different SEC filing types
"""

import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class FilingProcessor:
    """Base class for filing-specific processors"""
    
    def __init__(self):
        self.filing_type = "GENERIC"
    
    def extract_sections(self, html_content: str) -> Dict[str, str]:
        """Extract structured sections from filing"""
        return {"full_text": self.clean_html(html_content)}
    
    def clean_html(self, html_content: str) -> str:
        """Clean HTML content and extract text"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean up whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def identify_key_sections(self, text: str) -> Dict[str, str]:
        """Identify key sections in the filing"""
        return {"content": text}


class TenKProcessor(FilingProcessor):
    """Processor for 10-K annual reports"""
    
    def __init__(self):
        super().__init__()
        self.filing_type = "10-K"
    
    def extract_sections(self, html_content: str) -> Dict[str, str]:
        """Extract 10-K specific sections"""
        
        text = self.clean_html(html_content)
        sections = {}
        
        # 10-K section patterns
        section_patterns = {
            "business_overview": [
                r"item\s+1\s*[\.\-\s]*business",
                r"business\s+overview",
                r"our\s+business"
            ],
            "risk_factors": [
                r"item\s+1a\s*[\.\-\s]*risk\s+factors",
                r"risk\s+factors",
                r"principal\s+risks"
            ],
            "management_discussion": [
                r"item\s+7\s*[\.\-\s]*management['\s]*s\s+discussion",
                r"management['\s]*s\s+discussion\s+and\s+analysis",
                r"md&a"
            ],
            "financial_statements": [
                r"item\s+8\s*[\.\-\s]*financial\s+statements",
                r"consolidated\s+statements",
                r"financial\s+statements"
            ]
        }
        
        sections = self._extract_sections_by_patterns(text, section_patterns)
        sections["full_text"] = text
        
        return sections
    
    def _extract_sections_by_patterns(self, text: str, patterns: Dict[str, List[str]]) -> Dict[str, str]:
        """Extract sections using regex patterns"""
        
        sections = {}
        text_lower = text.lower()
        
        # First, find all section boundaries
        all_matches = []
        for section_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
                for match in matches:
                    all_matches.append((match.start(), section_name, pattern))
        
        # Sort matches by position
        all_matches.sort(key=lambda x: x[0])
        
        # Extract sections between boundaries
        for i, (start_pos, section_name, pattern) in enumerate(all_matches):
            # Find the end position (next section or end of document)
            if i + 1 < len(all_matches):
                end_pos = all_matches[i + 1][0]
            else:
                end_pos = len(text)
            
            # Extract section text
            section_text = text[start_pos:end_pos].strip()
            
            # Only include substantial sections and avoid duplicates
            if len(section_text) > 100 and section_name not in sections:
                sections[section_name] = section_text
        
        return sections


class TenQProcessor(FilingProcessor):
    """Processor for 10-Q quarterly reports"""
    
    def __init__(self):
        super().__init__()
        self.filing_type = "10-Q"
    
    def extract_sections(self, html_content: str) -> Dict[str, str]:
        """Extract 10-Q specific sections"""
        
        text = self.clean_html(html_content)
        sections = {}
        
        # 10-Q section patterns
        section_patterns = {
            "financial_statements": [
                r"item\s+1\s*[\.\-\s]*financial\s+statements",
                r"condensed\s+consolidated\s+statements",
                r"unaudited\s+financial\s+statements"
            ],
            "management_discussion": [
                r"item\s+2\s*[\.\-\s]*management['\s]*s\s+discussion",
                r"management['\s]*s\s+discussion\s+and\s+analysis",
                r"md&a"
            ],
            "controls_procedures": [
                r"item\s+4\s*[\.\-\s]*controls\s+and\s+procedures",
                r"disclosure\s+controls",
                r"internal\s+control"
            ]
        }
        
        sections = self._extract_sections_by_patterns(text, section_patterns)
        sections["full_text"] = text
        
        return sections
    
    def _extract_sections_by_patterns(self, text: str, patterns: Dict[str, List[str]]) -> Dict[str, str]:
        """Extract sections using regex patterns"""
        return TenKProcessor()._extract_sections_by_patterns(text, patterns)


class EightKProcessor(FilingProcessor):
    """Processor for 8-K current reports"""
    
    def __init__(self):
        super().__init__()
        self.filing_type = "8-K"
    
    def extract_sections(self, html_content: str) -> Dict[str, str]:
        """Extract 8-K specific sections"""
        
        text = self.clean_html(html_content)
        sections = {}
        
        # 8-K item patterns
        item_patterns = {
            "material_events": [
                r"item\s+[1-9]\s*[\.\-\s]*",
                r"material\s+events",
                r"corporate\s+changes"
            ],
            "financial_statements": [
                r"item\s+9\.01\s*[\.\-\s]*financial\s+statements",
                r"pro\s+forma\s+financial"
            ],
            "exhibits": [
                r"item\s+9\.01\s*[\.\-\s]*exhibits",
                r"signature",
                r"exhibit\s+index"
            ]
        }
        
        sections = self._extract_sections_by_patterns(text, item_patterns)
        sections["full_text"] = text
        
        return sections
    
    def _extract_sections_by_patterns(self, text: str, patterns: Dict[str, List[str]]) -> Dict[str, str]:
        """Extract sections using regex patterns"""
        return TenKProcessor()._extract_sections_by_patterns(text, patterns)


class ProxyProcessor(FilingProcessor):
    """Processor for DEF 14A proxy statements"""
    
    def __init__(self):
        super().__init__()
        self.filing_type = "DEF 14A"
    
    def extract_sections(self, html_content: str) -> Dict[str, str]:
        """Extract proxy statement specific sections"""
        
        text = self.clean_html(html_content)
        sections = {}
        
        # Proxy statement section patterns
        section_patterns = {
            "executive_compensation": [
                r"executive\s+compensation",
                r"compensation\s+discussion",
                r"summary\s+compensation\s+table",
                r"pay\s+ratio"
            ],
            "board_governance": [
                r"board\s+of\s+directors",
                r"corporate\s+governance",
                r"director\s+compensation",
                r"board\s+committees"
            ],
            "shareholder_matters": [
                r"shareholder\s+proposals",
                r"voting\s+matters",
                r"proposals\s+to\s+be\s+voted",
                r"annual\s+meeting"
            ],
            "audit_matters": [
                r"audit\s+committee",
                r"auditor\s+fees",
                r"independent\s+auditor"
            ]
        }
        
        sections = self._extract_sections_by_patterns(text, section_patterns)
        sections["full_text"] = text
        
        return sections
    
    def _extract_sections_by_patterns(self, text: str, patterns: Dict[str, List[str]]) -> Dict[str, str]:
        """Extract sections using regex patterns"""
        return TenKProcessor()._extract_sections_by_patterns(text, patterns)


class InsiderTradingProcessor(FilingProcessor):
    """Processor for Forms 3, 4, 5 (insider trading)"""
    
    def __init__(self, form_type: str = "4"):
        super().__init__()
        self.filing_type = form_type
    
    def extract_sections(self, html_content: str) -> Dict[str, str]:
        """Extract insider trading form sections"""
        
        text = self.clean_html(html_content)
        sections = {}
        
        # Insider trading form patterns
        section_patterns = {
            "reporting_person": [
                r"reporting\s+person",
                r"name\s+of\s+reporting\s+person",
                r"insider\s+information"
            ],
            "securities_owned": [
                r"securities\s+owned",
                r"beneficial\s+ownership",
                r"shares\s+owned"
            ],
            "transactions": [
                r"securities\s+acquired",
                r"securities\s+disposed",
                r"transaction\s+details",
                r"nature\s+of\s+ownership"
            ]
        }
        
        sections = self._extract_sections_by_patterns(text, section_patterns)
        sections["full_text"] = text
        
        return sections
    
    def _extract_sections_by_patterns(self, text: str, patterns: Dict[str, List[str]]) -> Dict[str, str]:
        """Extract sections using regex patterns"""
        return TenKProcessor()._extract_sections_by_patterns(text, patterns)


class FinancialContentIdentifier:
    """Enhanced financial content section identification"""
    
    def __init__(self):
        # Financial content patterns for enhanced identification
        self.financial_patterns = {
            "management_discussion": [
                r"management['\s]*s\s+discussion\s+and\s+analysis",
                r"md&a",
                r"results\s+of\s+operations",
                r"financial\s+condition\s+and\s+results",
                r"liquidity\s+and\s+capital\s+resources",
                r"critical\s+accounting\s+policies"
            ],
            "risk_factors": [
                r"risk\s+factors",
                r"principal\s+risks",
                r"material\s+risks",
                r"factors\s+that\s+may\s+affect",
                r"forward[.\s-]*looking\s+statements",
                r"uncertainties\s+and\s+risks"
            ],
            "financial_statements": [
                r"consolidated\s+statements",
                r"financial\s+statements",
                r"balance\s+sheet",
                r"income\s+statement",
                r"cash\s+flow\s+statement",
                r"statements\s+of\s+operations",
                r"statements\s+of\s+equity",
                r"notes\s+to\s+financial\s+statements"
            ],
            "executive_compensation": [
                r"executive\s+compensation",
                r"compensation\s+discussion",
                r"summary\s+compensation\s+table",
                r"named\s+executive\s+officers",
                r"pay\s+ratio",
                r"compensation\s+committee",
                r"equity\s+compensation",
                r"stock\s+option\s+grants"
            ],
            "business_overview": [
                r"business\s+overview",
                r"our\s+business",
                r"company\s+overview",
                r"business\s+description",
                r"products\s+and\s+services",
                r"business\s+segments",
                r"competitive\s+strengths"
            ],
            "governance": [
                r"corporate\s+governance",
                r"board\s+of\s+directors",
                r"audit\s+committee",
                r"governance\s+principles",
                r"director\s+independence",
                r"board\s+committees"
            ]
        }
    
    def identify_financial_content_type(self, text: str) -> List[str]:
        """Identify types of financial content in text"""
        
        content_types = []
        text_lower = text.lower()
        
        for content_type, patterns in self.financial_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    content_types.append(content_type)
                    break
        
        return content_types
    
    def extract_financial_metrics(self, text: str) -> Dict[str, List[str]]:
        """Extract financial metrics and concepts from text"""
        
        metrics = {
            "revenue_metrics": [],
            "profitability_metrics": [],
            "financial_ratios": [],
            "growth_metrics": []
        }
        
        # Revenue patterns
        revenue_patterns = [
            r"revenue\s+(?:of\s+)?\$?[\d,]+(?:\.\d+)?\s*(?:million|billion)?",
            r"net\s+sales\s+(?:of\s+)?\$?[\d,]+(?:\.\d+)?\s*(?:million|billion)?",
            r"total\s+revenue\s+(?:increased|decreased)\s+(?:by\s+)?[\d.]+%",
            r"revenue\s+growth\s+(?:of\s+)?[\d.]+%"
        ]
        
        # Profitability patterns
        profit_patterns = [
            r"net\s+income\s+(?:of\s+)?\$?[\d,]+(?:\.\d+)?\s*(?:million|billion)?",
            r"operating\s+income\s+(?:of\s+)?\$?[\d,]+(?:\.\d+)?\s*(?:million|billion)?",
            r"gross\s+profit\s+(?:margin\s+)?(?:of\s+)?[\d.]+%",
            r"operating\s+margin\s+(?:of\s+)?[\d.]+%"
        ]
        
        # Extract metrics
        for pattern in revenue_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            metrics["revenue_metrics"].extend(matches)
        
        for pattern in profit_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            metrics["profitability_metrics"].extend(matches)
        
        return metrics
    
    def calculate_content_quality_score(self, text: str, filing_type: str) -> float:
        """Calculate quality score for financial content"""
        
        score = 0.0
        text_lower = text.lower()
        
        # Base score for length (more generous)
        word_count = len(text.split())
        if word_count > 1000:
            score += 0.4
        elif word_count > 500:
            score += 0.3
        elif word_count > 200:
            score += 0.2
        elif word_count > 50:
            score += 0.1
        
        # Score for financial content types (more generous)
        content_types = self.identify_financial_content_type(text)
        score += len(content_types) * 0.15
        
        # Score for financial metrics
        metrics = self.extract_financial_metrics(text)
        total_metrics = sum(len(metric_list) for metric_list in metrics.values())
        score += min(total_metrics * 0.08, 0.4)
        
        # Filing-specific scoring (more generous)
        if filing_type == "10-K":
            # 10-K should have comprehensive content
            required_sections = ["business_overview", "risk_factors", "management_discussion"]
            found_sections = [s for s in required_sections if s in content_types]
            score += len(found_sections) * 0.15
        
        elif filing_type == "DEF 14A":
            # Proxy statements should have governance content
            if "executive_compensation" in content_types:
                score += 0.25
            if "governance" in content_types:
                score += 0.25
        
        elif filing_type == "10-Q":
            # Quarterly reports should have financial content
            if "management_discussion" in content_types:
                score += 0.2
            if "financial_statements" in content_types:
                score += 0.2
        
        # Bonus for having multiple types of financial content
        if len(content_types) >= 2:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0


class FilingProcessorFactory:
    """Factory for creating filing-specific processors"""
    
    @staticmethod
    def get_processor(filing_type: str) -> FilingProcessor:
        """Get appropriate processor for filing type"""
        
        processors = {
            "10-K": TenKProcessor,
            "10-Q": TenQProcessor,
            "8-K": EightKProcessor,
            "DEF 14A": ProxyProcessor,
            "3": lambda: InsiderTradingProcessor("3"),
            "4": lambda: InsiderTradingProcessor("4"),
            "5": lambda: InsiderTradingProcessor("5")
        }
        
        processor_class = processors.get(filing_type, FilingProcessor)
        return processor_class()
    
    @staticmethod
    def get_supported_types() -> List[str]:
        """Get list of supported filing types"""
        return ["10-K", "10-Q", "8-K", "DEF 14A", "3", "4", "5"]
    
    @staticmethod
    def get_financial_content_identifier() -> FinancialContentIdentifier:
        """Get financial content identifier instance"""
        return FinancialContentIdentifier()