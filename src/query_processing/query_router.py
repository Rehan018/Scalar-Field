from typing import Dict, List, Optional
from enum import Enum

from .entity_extractor import EntityExtractor
from vector_store.retrieval import RetrievalEngine


class QueryType(Enum):
    SINGLE_COMPANY = "single_company"
    MULTI_COMPANY = "multi_company"
    TEMPORAL_ANALYSIS = "temporal_analysis"
    CROSS_SECTIONAL = "cross_sectional"
    GENERAL_SEARCH = "general_search"


class QueryRouter:
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.retrieval_engine = RetrievalEngine()
    
    def route_query(self, query: str) -> Dict:
        
        entities = self.entity_extractor.extract_all_entities(query)
        
        query_type = self._determine_query_type(entities)
        
        relevant_docs = self._retrieve_relevant_documents(query, entities, query_type)
        
        return {
            "query": query,
            "entities": entities,
            "query_type": query_type.value,
            "relevant_documents": relevant_docs,
            "processing_strategy": self._get_processing_strategy(query_type, entities)
        }
    
    def _determine_query_type(self, entities: Dict) -> QueryType:
        
        tickers = entities["tickers"]
        time_periods = entities["time_periods"]
        comparison_intent = entities["comparison_intent"]
        
        if len(tickers) > 1 or comparison_intent["is_comparison"]:
            if comparison_intent["comparison_type"] == "temporal":
                return QueryType.TEMPORAL_ANALYSIS
            else:
                return QueryType.MULTI_COMPANY
        
        elif len(tickers) == 1 and (time_periods["years"] or time_periods["relative_terms"]):
            return QueryType.TEMPORAL_ANALYSIS
        
        elif len(tickers) == 1:
            return QueryType.SINGLE_COMPANY
        
        elif entities["financial_concepts"]:
            return QueryType.CROSS_SECTIONAL
        
        else:
            return QueryType.GENERAL_SEARCH
    
    def _retrieve_relevant_documents(self, query: str, entities: Dict, 
                                   query_type: QueryType) -> List[Dict]:
        
        tickers = entities["tickers"]
        filing_types = entities["filing_types"]
        time_periods = entities["time_periods"]
        
        if query_type == QueryType.SINGLE_COMPANY:
            return self._retrieve_single_company(query, tickers[0], filing_types, time_periods)
        
        elif query_type == QueryType.MULTI_COMPANY:
            return self._retrieve_multi_company(query, tickers, filing_types)
        
        elif query_type == QueryType.TEMPORAL_ANALYSIS:
            return self._retrieve_temporal(query, tickers, time_periods)
        
        elif query_type == QueryType.CROSS_SECTIONAL:
            return self._retrieve_cross_sectional(query, entities["financial_concepts"])
        
        else:
            return self._retrieve_general(query)
    
    def _retrieve_single_company(self, query: str, ticker: str, 
                               filing_types: List[str], 
                               time_periods: Dict) -> List[Dict]:
        
        filters = {"ticker": ticker}
        
        if filing_types:
            filters["filing_type"] = filing_types[0]
        
        date_range = None
        if time_periods["years"]:
            year = time_periods["years"][0]
            date_range = (f"{year}-01-01", f"{year}-12-31")
        
        return self.retrieval_engine.search_with_filters(
            query, ticker=ticker, 
            filing_type=filing_types[0] if filing_types else None,
            date_range=date_range,
            n_results=15
        )
    
    def _retrieve_multi_company(self, query: str, tickers: List[str], 
                              filing_types: List[str]) -> List[Dict]:
        
        all_results = []
        
        if not tickers:
            return self._retrieve_general(query)
        
        results_per_company = max(5, 20 // len(tickers))
        
        for ticker in tickers:
            company_results = self.retrieval_engine.search_with_filters(
                query, ticker=ticker,
                filing_type=filing_types[0] if filing_types else None,
                n_results=results_per_company
            )
            all_results.extend(company_results)
        
        all_results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return all_results[:20]
    
    def _retrieve_temporal(self, query: str, tickers: List[str], 
                         time_periods: Dict) -> List[Dict]:
        
        results = []
        
        if tickers:
            ticker = tickers[0]
            
            if time_periods["years"]:
                for year in time_periods["years"]:
                    year_results = self.retrieval_engine.search_temporal(
                        query, year=int(year)
                    )
                    results.extend(year_results)
            else:
                results = self.retrieval_engine.search_with_filters(
                    query, ticker=ticker, n_results=20
                )
        else:
            results = self.retrieval_engine.search_temporal(query)
        
        return results[:20]
    
    def _retrieve_cross_sectional(self, query: str, 
                                concepts: List[str]) -> List[Dict]:
        
        results = self.retrieval_engine.hybrid_search(
            query, keyword_boost=0.4, n_results=25
        )
        
        return results
    
    def _retrieve_general(self, query: str) -> List[Dict]:
        
        return self.retrieval_engine.hybrid_search(
            query, keyword_boost=0.3, n_results=15
        )
    
    def _get_processing_strategy(self, query_type: QueryType, 
                               entities: Dict) -> Dict:
        
        strategies = {
            QueryType.SINGLE_COMPANY: {
                "approach": "focused_analysis",
                "synthesis_method": "single_source",
                "context_window": "company_specific"
            },
            QueryType.MULTI_COMPANY: {
                "approach": "comparative_analysis",
                "synthesis_method": "cross_company",
                "context_window": "multi_entity"
            },
            QueryType.TEMPORAL_ANALYSIS: {
                "approach": "time_series_analysis",
                "synthesis_method": "temporal_synthesis",
                "context_window": "chronological"
            },
            QueryType.CROSS_SECTIONAL: {
                "approach": "thematic_analysis",
                "synthesis_method": "concept_aggregation",
                "context_window": "industry_wide"
            },
            QueryType.GENERAL_SEARCH: {
                "approach": "broad_search",
                "synthesis_method": "relevance_ranking",
                "context_window": "general"
            }
        }
        
        return strategies.get(query_type, strategies[QueryType.GENERAL_SEARCH])
    
    def get_query_complexity(self, entities: Dict) -> str:
        
        complexity_score = 0
        
        complexity_score += len(entities["tickers"]) * 2
        
        complexity_score += len(entities["time_periods"]["years"])
        
        complexity_score += len(entities["filing_types"])
        
        if entities["comparison_intent"]["is_comparison"]:
            complexity_score += 3
        
        complexity_score += len(entities["financial_concepts"])
        
        if complexity_score <= 3:
            return "simple"
        elif complexity_score <= 7:
            return "moderate"
        else:
            return "complex"