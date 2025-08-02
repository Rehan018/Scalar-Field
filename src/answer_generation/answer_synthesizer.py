from typing import Dict, List, Optional
import re

from .llm_client import LLMClient
from .prompt_templates import PromptTemplates
from .source_attribution import SourceAttributor
from query_processing.query_router import QueryType


class AnswerSynthesizer:
    def __init__(self):
        self.llm_client = LLMClient()
        self.prompt_templates = PromptTemplates()
        self.source_attributor = SourceAttributor()
    
    def synthesize_answer(self, query_analysis: Dict) -> Dict:
        """Synthesize answer based on query analysis."""
        
        query = query_analysis["query"]
        entities = query_analysis["entities"]
        query_type = query_analysis["query_type"]
        relevant_docs = query_analysis["relevant_documents"]
        
        if not relevant_docs:
            return {
                "answer": "I couldn't find relevant information in the SEC filings to answer your question.",
                "confidence": 0.0,
                "sources": [],
                "status": "no_relevant_docs"
            }
        
        # Generate appropriate prompt based on query type
        prompt = self._generate_prompt(query, entities, query_type, relevant_docs)
        
        # Get LLM response
        llm_response = self.llm_client.generate_answer(prompt)
        
        if llm_response["status"] != "success":
            return {
                "answer": llm_response["answer"],
                "confidence": 0.0,
                "sources": [],
                "status": "llm_error",
                "error": llm_response.get("error")
            }
        
        # Process and enhance the answer
        processed_answer = self._process_answer(
            llm_response["answer"], relevant_docs, entities
        )
        
        # Generate source attribution
        sources = self.source_attributor.generate_citations(relevant_docs)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(
            processed_answer, relevant_docs, llm_response
        )
        
        return {
            "answer": processed_answer,
            "confidence": confidence,
            "sources": sources,
            "query_type": query_type,
            "tokens_used": llm_response.get("tokens_used", 0),
            "status": "success"
        }
    
    def _generate_prompt(self, query: str, entities: Dict, 
                        query_type: str, relevant_docs: List[Dict]) -> str:
        """Generate appropriate prompt based on query type."""
        
        tickers = entities["tickers"]
        financial_concepts = entities["financial_concepts"]
        time_periods = entities["time_periods"]["years"]
        
        if query_type == QueryType.SINGLE_COMPANY.value and tickers:
            ticker = tickers[0]
            company_name = entities.get("company_name", ticker)
            return self.prompt_templates.single_company_analysis(
                query, company_name, ticker, relevant_docs
            )
        
        elif query_type == QueryType.MULTI_COMPANY.value and len(tickers) > 1:
            return self.prompt_templates.multi_company_comparison(
                query, tickers, relevant_docs
            )
        
        elif query_type == QueryType.TEMPORAL_ANALYSIS.value:
            ticker = tickers[0] if tickers else "Multiple Companies"
            return self.prompt_templates.temporal_analysis(
                query, ticker, time_periods, relevant_docs
            )
        
        elif query_type == QueryType.CROSS_SECTIONAL.value:
            return self.prompt_templates.cross_sectional_analysis(
                query, financial_concepts, relevant_docs
            )
        
        # Check for specific analysis types
        elif "risk" in query.lower():
            return self.prompt_templates.risk_factor_analysis(query, relevant_docs)
        
        elif any(term in query.lower() for term in ["revenue", "profit", "cash", "debt", "financial"]):
            return self.prompt_templates.financial_metrics_analysis(query, relevant_docs)
        
        else:
            return self.prompt_templates.general_qa_template(query, relevant_docs)
    
    def _process_answer(self, raw_answer: str, relevant_docs: List[Dict], 
                       entities: Dict) -> str:
        """Process and enhance the raw LLM answer."""
        
        # Clean up the answer
        processed_answer = raw_answer.strip()
        
        # Add uncertainty indicators where appropriate
        processed_answer = self._add_uncertainty_indicators(processed_answer)
        
        # Ensure proper formatting
        processed_answer = self._format_answer(processed_answer)
        
        return processed_answer
    
    def _add_uncertainty_indicators(self, answer: str) -> str:
        """Add appropriate uncertainty indicators to the answer."""
        
        # Patterns that might indicate uncertainty
        uncertain_patterns = [
            r'\bmay\b', r'\bmight\b', r'\bcould\b', r'\bpossibly\b',
            r'\blikely\b', r'\bunlikely\b', r'\bappears\b', r'\bseems\b'
        ]
        
        # If answer contains uncertain language, ensure it's appropriately qualified
        has_uncertainty = any(re.search(pattern, answer, re.IGNORECASE) 
                            for pattern in uncertain_patterns)
        
        if has_uncertainty and not any(phrase in answer.lower() 
                                     for phrase in ["based on available", "according to", "note that"]):
            # Add a qualification if not already present
            if not answer.startswith("Based on"):
                answer = "Based on the available SEC filing information, " + answer.lower()
        
        return answer
    
    def _format_answer(self, answer: str) -> str:
        """Format the answer for better readability."""
        
        # Ensure proper paragraph breaks
        answer = re.sub(r'\n\s*\n\s*\n+', '\n\n', answer)
        
        # Clean up extra whitespace
        answer = re.sub(r' +', ' ', answer)
        
        # Ensure proper sentence spacing
        answer = re.sub(r'\.([A-Z])', r'. \1', answer)
        
        return answer.strip()
    
    def _calculate_confidence(self, answer: str, relevant_docs: List[Dict], 
                            llm_response: Dict) -> float:
        """Calculate confidence score for the answer."""
        
        confidence_factors = []
        
        # Factor 1: Number of relevant documents
        doc_factor = min(1.0, len(relevant_docs) / 5.0)
        confidence_factors.append(doc_factor * 0.3)
        
        # Factor 2: Average similarity of retrieved documents
        if relevant_docs:
            avg_similarity = sum(doc.get("similarity", 0) for doc in relevant_docs) / len(relevant_docs)
            confidence_factors.append(avg_similarity * 0.3)
        
        # Factor 3: Answer length and detail (longer answers often more confident)
        length_factor = min(1.0, len(answer.split()) / 200.0)
        confidence_factors.append(length_factor * 0.2)
        
        # Factor 4: Presence of specific data/numbers (indicates concrete information)
        has_numbers = bool(re.search(r'\d+', answer))
        has_percentages = bool(re.search(r'\d+%', answer))
        has_dates = bool(re.search(r'\d{4}', answer))
        
        specificity_factor = (has_numbers + has_percentages + has_dates) / 3.0
        confidence_factors.append(specificity_factor * 0.2)
        
        # Calculate overall confidence
        total_confidence = sum(confidence_factors)
        
        # Apply penalties for uncertainty indicators
        uncertainty_penalties = [
            ("I don't have enough information", -0.3),
            ("unable to determine", -0.2),
            ("insufficient data", -0.2),
            ("may", -0.05),
            ("might", -0.05),
            ("possibly", -0.05)
        ]
        
        for phrase, penalty in uncertainty_penalties:
            if phrase.lower() in answer.lower():
                total_confidence += penalty
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, total_confidence))
    
    def generate_follow_up_questions(self, query: str, answer: str, 
                                   entities: Dict) -> List[str]:
        """Generate relevant follow-up questions."""
        
        follow_ups = []
        tickers = entities["tickers"]
        financial_concepts = entities["financial_concepts"]
        
        # Company-specific follow-ups
        if tickers:
            ticker = tickers[0]
            follow_ups.extend([
                f"What are the main risk factors for {ticker}?",
                f"How has {ticker}'s financial performance changed over time?",
                f"What does {ticker} say about future outlook?"
            ])
        
        # Concept-specific follow-ups
        if "revenue" in financial_concepts:
            follow_ups.append("What are the main revenue drivers mentioned?")
        
        if "risk" in financial_concepts:
            follow_ups.append("How do these risks compare across different companies?")
        
        # Comparative follow-ups
        if len(tickers) > 1:
            follow_ups.append("Which company appears to be performing better and why?")
        
        return follow_ups[:3]  # Return top 3 follow-ups