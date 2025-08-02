from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
import os


class HTMLParser:
    def __init__(self):
        self.soup = None
        
    def parse_file(self, filepath: str) -> Dict:
        """Parse SEC HTML filing and extract structured content."""
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse_content(content, filepath)
            
        except Exception as e:
            print(f"Error parsing file {filepath}: {e}")
            return {"error": str(e), "filepath": filepath}
    
    def parse_content(self, html_content: str, source_path: str = "") -> Dict:
        """Parse HTML content and extract structured information."""
        
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic document info
        doc_info = self._extract_document_info()
        
        # Extract main content sections
        sections = self._extract_sections()
        
        # Extract tables
        tables = self._extract_tables()
        
        # Clean and combine all text
        full_text = self._extract_clean_text()
        
        return {
            "source_path": source_path,
            "document_info": doc_info,
            "sections": sections,
            "tables": tables,
            "full_text": full_text,
            "word_count": len(full_text.split()),
            "parsing_status": "success"
        }
    
    def _extract_document_info(self) -> Dict:
        """Extract basic document metadata."""
        
        info = {}
        
        # Try to find document title
        title_tag = self.soup.find('title')
        if title_tag:
            info['title'] = title_tag.get_text().strip()
        
        # Look for company name in various places
        company_patterns = [
            r'COMPANY\s+CONFORMED\s+NAME:\s*([^\n]+)',
            r'REGISTRANT\s+NAME:\s*([^\n]+)',
            r'FILER:\s*([^\n]+)'
        ]
        
        text = self.soup.get_text()
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['company_name'] = match.group(1).strip()
                break
        
        # Extract filing date
        date_patterns = [
            r'FILED\s+AS\s+OF\s+DATE:\s*(\d{8})',
            r'FILING\s+DATE:\s*(\d{4}-\d{2}-\d{2})',
            r'DATE\s+OF\s+REPORT:\s*(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['filing_date'] = match.group(1).strip()
                break
        
        # Extract form type
        form_match = re.search(r'FORM\s+TYPE:\s*([^\n]+)', text, re.IGNORECASE)
        if form_match:
            info['form_type'] = form_match.group(1).strip()
        
        return info
    
    def _extract_sections(self) -> List[Dict]:
        """Extract major document sections."""
        
        sections = []
        
        # Common SEC filing section patterns
        section_patterns = [
            (r'PART\s+I\b', 'Part I'),
            (r'PART\s+II\b', 'Part II'),
            (r'PART\s+III\b', 'Part III'),
            (r'PART\s+IV\b', 'Part IV'),
            (r'ITEM\s+\d+[A-Z]?\b', 'Item'),
            (r'RISK\s+FACTORS', 'Risk Factors'),
            (r'MANAGEMENT.S\s+DISCUSSION', 'MD&A'),
            (r'BUSINESS\s+OVERVIEW', 'Business'),
            (r'FINANCIAL\s+STATEMENTS', 'Financial Statements'),
            (r'NOTES\s+TO\s+FINANCIAL', 'Notes to Financial Statements')
        ]
        
        text = self.soup.get_text()
        
        for pattern, section_type in section_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                start_pos = match.start()
                section_title = text[start_pos:start_pos+100].split('\n')[0].strip()
                
                sections.append({
                    'type': section_type,
                    'title': section_title,
                    'start_position': start_pos,
                    'pattern_matched': pattern
                })
        
        # Sort sections by position
        sections.sort(key=lambda x: x['start_position'])
        
        return sections
    
    def _extract_tables(self) -> List[Dict]:
        """Extract and parse HTML tables."""
        
        tables = []
        table_tags = self.soup.find_all('table')
        
        for i, table in enumerate(table_tags):
            try:
                rows = []
                for row in table.find_all('tr'):
                    cells = []
                    for cell in row.find_all(['td', 'th']):
                        cells.append(cell.get_text().strip())
                    if cells:  # Only add non-empty rows
                        rows.append(cells)
                
                if rows:  # Only add tables with content
                    tables.append({
                        'table_id': i,
                        'rows': rows,
                        'row_count': len(rows),
                        'column_count': max(len(row) for row in rows) if rows else 0
                    })
                    
            except Exception as e:
                print(f"Error parsing table {i}: {e}")
                continue
        
        return tables
    
    def _extract_clean_text(self) -> str:
        """Extract and clean all text content."""
        
        # Remove script and style elements
        for script in self.soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it
        text = self.soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_section_text(self, section_title: str) -> Optional[str]:
        """Extract text from a specific section."""
        
        if not self.soup:
            return None
        
        text = self.soup.get_text()
        
        # Find section start
        section_match = re.search(
            rf'{re.escape(section_title)}.*?(?=\n|\r)', 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        
        if not section_match:
            return None
        
        start_pos = section_match.end()
        
        # Find next major section (rough heuristic)
        next_section_patterns = [
            r'\n\s*ITEM\s+\d+',
            r'\n\s*PART\s+[IVX]+',
            r'\n\s*[A-Z\s]{10,}\n'
        ]
        
        end_pos = len(text)
        for pattern in next_section_patterns:
            match = re.search(pattern, text[start_pos:], re.IGNORECASE)
            if match:
                end_pos = start_pos + match.start()
                break
        
        section_text = text[start_pos:end_pos].strip()
        return section_text if len(section_text) > 50 else None