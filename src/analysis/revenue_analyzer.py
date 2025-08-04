"""
Revenue Analysis Module for SEC Filings QA System
Implements revenue driver identification, trend analysis, and cross-company comparisons.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json

@dataclass
class RevenueMetric:
    """Data class for revenue metrics"""
    company: str
    filing_type: str
    filing_date: str
    metric_type: str  # 'total_revenue', 'segment_revenue', 'growth_rate', etc.
    value: float
    unit: str  # 'billion', 'million', 'percent'
    context: str  # Original text context
    source_section: str  # Which section it came from

@dataclass
class RevenueDriver:
    """Data class for revenue drivers"""
    company: str
    driver_type: str  # 'product', 'service', 'geographic', 'customer_segment'
    driver_name: str
    description: str
    importance: float  # 0.0 to 1.0 based on context analysis
    trend: str  # 'growing', 'declining', 'stable'
    source_context: str

@dataclass
class RDSpendingMetric:
    """Data class for R&D spending metrics"""
    company: str
    filing_type: str
    filing_date: str
    metric_type: str  # 'rd_expense', 'rd_percentage', 'rd_growth_rate'
    value: float
    unit: str  # 'billion', 'million', 'percent'
    context: str  # Original text context
    source_section: str  # Which section it came from

@dataclass
class InnovationStrategy:
    """Data class for innovation investment strategies"""
    company: str
    strategy_type: str  # 'technology_focus', 'acquisition', 'partnership', 'internal_development'
    strategy_name: str
    description: str
    investment_level: str  # 'high', 'medium', 'low'
    focus_areas: List[str]  # Areas of innovation focus
    source_context: str

class RevenueAnalyzer:
    """Comprehensive revenue and R&D analysis for SEC filings"""
    
    def __init__(self):
        self.revenue_patterns = self._initialize_revenue_patterns()
        self.driver_patterns = self._initialize_driver_patterns()
        self.trend_patterns = self._initialize_trend_patterns()
        self.rd_patterns = self._initialize_rd_patterns()
        self.innovation_patterns = self._initialize_innovation_patterns()
        
    def _initialize_revenue_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for revenue identification"""
        
        return {
            "total_revenue": [
                r"total\s+revenue\s+(?:of\s+|was\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million)",
                r"net\s+sales\s+(?:of\s+|were\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million)",
                r"revenue\s+(?:of\s+|was\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million)",
                r"total\s+net\s+sales\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million)"
            ],
            "revenue_growth": [
                r"revenue\s+(?:increased|grew|growth)\s+(?:by\s+)?([\d.]+)%",
                r"(?:increase|growth)\s+in\s+revenue\s+of\s+([\d.]+)%",
                r"revenue\s+growth\s+(?:of\s+|was\s+)?([\d.]+)%",
                r"([\d.]+)%\s+(?:increase|growth)\s+in\s+revenue"
            ],
            "segment_revenue": [
                r"([a-zA-Z\s]+)\s+revenue\s+(?:of\s+|was\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million)",
                r"([a-zA-Z\s]+)\s+segment\s+revenue\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million)",
                r"revenue\s+from\s+([a-zA-Z\s]+)\s+(?:of\s+|was\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million)"
            ]
        }
    
    def _initialize_driver_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for revenue driver identification"""
        
        return {
            "product_drivers": [
                r"(?:driven\s+by|primarily\s+from|growth\s+in)\s+([a-zA-Z\s]+)\s+(?:sales|revenue|products)",
                r"([a-zA-Z\s]+)\s+(?:products|services)\s+(?:contributed|drove|generated)",
                r"strong\s+(?:performance|growth)\s+in\s+([a-zA-Z\s]+)",
                r"([a-zA-Z\s]+)\s+business\s+(?:grew|increased|expanded)"
            ],
            "service_drivers": [
                r"(?:services|subscription|cloud|software)\s+revenue\s+(?:from|of)\s+([a-zA-Z\s]+)",
                r"([a-zA-Z\s]+)\s+services\s+(?:contributed|generated|drove)",
                r"growth\s+in\s+([a-zA-Z\s]+)\s+services",
                r"([a-zA-Z\s]+)\s+subscription\s+(?:revenue|growth)"
            ],
            "geographic_drivers": [
                r"(?:revenue|sales)\s+in\s+([a-zA-Z\s]+)\s+(?:increased|grew|expanded)",
                r"([a-zA-Z\s]+)\s+(?:market|region)\s+(?:contributed|drove|generated)",
                r"strong\s+(?:performance|growth)\s+in\s+([a-zA-Z\s]+)",
                r"international\s+revenue\s+from\s+([a-zA-Z\s]+)"
            ],
            "customer_drivers": [
                r"([a-zA-Z\s]+)\s+customers\s+(?:contributed|drove|generated)",
                r"growth\s+in\s+([a-zA-Z\s]+)\s+customer\s+base",
                r"([a-zA-Z\s]+)\s+segment\s+customers",
                r"enterprise\s+customers\s+in\s+([a-zA-Z\s]+)"
            ]
        }
    
    def _initialize_trend_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for trend identification"""
        
        return {
            "growing": [
                r"increased|grew|growth|expansion|rising|uptick|improvement|strong|robust",
                r"accelerat|momentum|outperform|exceed|beat|surpass"
            ],
            "declining": [
                r"decreased|declined|drop|fell|weakness|softness|challenging|pressure",
                r"decelerat|slowdown|underperform|miss|below|contract"
            ],
            "stable": [
                r"stable|consistent|maintained|steady|flat|unchanged|similar",
                r"in\s+line\s+with|comparable|equivalent"
            ]
        }
    
    def analyze_revenue_metrics(self, chunks: List) -> List[RevenueMetric]:
        """Extract revenue metrics from document chunks"""
        
        metrics = []
        
        for chunk in chunks:
            content = chunk.content
            metadata = chunk.metadata
            
            company = metadata.get('ticker', 'Unknown')
            filing_type = metadata.get('filing_type', 'Unknown')
            filing_date = metadata.get('filing_date', 'Unknown')
            section_type = metadata.get('section_type', 'Unknown')
            
            # Extract different types of revenue metrics
            for metric_type, patterns in self.revenue_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        try:
                            if metric_type == "segment_revenue":
                                segment_name = match.group(1).strip()
                                value = float(match.group(2).replace(',', ''))
                                unit = match.group(3).lower()
                                context = match.group(0)
                                
                                metric = RevenueMetric(
                                    company=company,
                                    filing_type=filing_type,
                                    filing_date=filing_date,
                                    metric_type=f"{segment_name.lower()}_revenue",
                                    value=value,
                                    unit=unit,
                                    context=context,
                                    source_section=section_type
                                )
                                metrics.append(metric)
                                
                            elif metric_type == "revenue_growth":
                                value = float(match.group(1))
                                context = match.group(0)
                                
                                metric = RevenueMetric(
                                    company=company,
                                    filing_type=filing_type,
                                    filing_date=filing_date,
                                    metric_type="revenue_growth_rate",
                                    value=value,
                                    unit="percent",
                                    context=context,
                                    source_section=section_type
                                )
                                metrics.append(metric)
                                
                            else:  # total_revenue
                                value = float(match.group(1).replace(',', ''))
                                unit = match.group(2).lower()
                                context = match.group(0)
                                
                                metric = RevenueMetric(
                                    company=company,
                                    filing_type=filing_type,
                                    filing_date=filing_date,
                                    metric_type=metric_type,
                                    value=value,
                                    unit=unit,
                                    context=context,
                                    source_section=section_type
                                )
                                metrics.append(metric)
                                
                        except (ValueError, IndexError) as e:
                            # Skip invalid matches
                            continue
        
        return metrics
    
    def identify_revenue_drivers(self, chunks: List) -> List[RevenueDriver]:
        """Identify revenue drivers from document chunks"""
        
        drivers = []
        
        for chunk in chunks:
            content = chunk.content
            metadata = chunk.metadata
            
            company = metadata.get('ticker', 'Unknown')
            section_type = metadata.get('section_type', 'Unknown')
            
            # Only analyze relevant sections
            if section_type not in ['management_analysis', 'business', 'financial']:
                continue
            
            # Extract different types of revenue drivers
            for driver_type, patterns in self.driver_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        try:
                            driver_name = match.group(1).strip()
                            
                            # Skip very short or generic names
                            if len(driver_name) < 3 or driver_name.lower() in ['the', 'our', 'and', 'or']:
                                continue
                            
                            # Get surrounding context for better analysis
                            start = max(0, match.start() - 100)
                            end = min(len(content), match.end() + 100)
                            context = content[start:end]
                            
                            # Determine trend and importance
                            trend = self._analyze_trend(context)
                            importance = self._calculate_importance(context, driver_name)
                            
                            driver = RevenueDriver(
                                company=company,
                                driver_type=driver_type.replace('_drivers', ''),
                                driver_name=driver_name,
                                description=match.group(0),
                                importance=importance,
                                trend=trend,
                                source_context=context
                            )
                            drivers.append(driver)
                            
                        except (IndexError, AttributeError):
                            continue
        
        return drivers
    
    def _analyze_trend(self, context: str) -> str:
        """Analyze trend from context"""
        
        context_lower = context.lower()
        
        # Count trend indicators
        trend_scores = {}
        for trend, patterns in self.trend_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, context_lower)
                score += len(matches)
            trend_scores[trend] = score
        
        # Return trend with highest score
        if max(trend_scores.values()) == 0:
            return "stable"
        
        return max(trend_scores, key=trend_scores.get)
    
    def _calculate_importance(self, context: str, driver_name: str) -> float:
        """Calculate importance score for a revenue driver"""
        
        importance = 0.5  # Base importance
        context_lower = context.lower()
        driver_lower = driver_name.lower()
        
        # Boost importance based on context indicators
        high_importance_indicators = [
            "primary", "main", "key", "major", "significant", "substantial",
            "largest", "biggest", "most important", "critical", "core"
        ]
        
        for indicator in high_importance_indicators:
            if indicator in context_lower:
                importance += 0.1
        
        # Boost if driver name appears multiple times
        driver_mentions = context_lower.count(driver_lower)
        importance += min(driver_mentions * 0.05, 0.2)
        
        # Boost for specific financial terms
        financial_terms = ["revenue", "sales", "income", "growth", "profit"]
        for term in financial_terms:
            if term in context_lower:
                importance += 0.05
        
        return min(importance, 1.0)
    
    def analyze_revenue_trends(self, metrics: List[RevenueMetric]) -> Dict[str, Dict]:
        """Analyze revenue trends across companies and time periods"""
        
        trends = defaultdict(lambda: defaultdict(list))
        
        # Group metrics by company and metric type
        for metric in metrics:
            trends[metric.company][metric.metric_type].append(metric)
        
        # Calculate trends for each company
        trend_analysis = {}
        
        for company, company_metrics in trends.items():
            company_trends = {}
            
            for metric_type, metric_list in company_metrics.items():
                # Sort by date
                sorted_metrics = sorted(metric_list, key=lambda x: x.filing_date)
                
                if len(sorted_metrics) >= 2:
                    # Calculate trend
                    first_value = sorted_metrics[0].value
                    last_value = sorted_metrics[-1].value
                    
                    if first_value > 0:
                        growth_rate = ((last_value - first_value) / first_value) * 100
                        
                        company_trends[metric_type] = {
                            "growth_rate": growth_rate,
                            "trend_direction": "growing" if growth_rate > 0 else "declining",
                            "data_points": len(sorted_metrics),
                            "latest_value": last_value,
                            "latest_unit": sorted_metrics[-1].unit,
                            "time_period": f"{sorted_metrics[0].filing_date} to {sorted_metrics[-1].filing_date}"
                        }
            
            trend_analysis[company] = company_trends
        
        return trend_analysis
    
    def compare_revenue_across_companies(self, metrics: List[RevenueMetric], 
                                       companies: List[str] = None) -> Dict:
        """Compare revenue metrics across companies"""
        
        if companies is None:
            companies = list(set(metric.company for metric in metrics))
        
        comparison = {
            "companies": companies,
            "metrics_comparison": {},
            "rankings": {},
            "insights": []
        }
        
        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in metrics:
            if metric.company in companies:
                metrics_by_type[metric.metric_type].append(metric)
        
        # Compare each metric type
        for metric_type, metric_list in metrics_by_type.items():
            # Get latest metric for each company
            latest_metrics = {}
            for metric in metric_list:
                company = metric.company
                if company not in latest_metrics or metric.filing_date > latest_metrics[company].filing_date:
                    latest_metrics[company] = metric
            
            if len(latest_metrics) >= 2:
                # Create comparison
                company_values = []
                for company, metric in latest_metrics.items():
                    # Normalize to billions for comparison
                    normalized_value = metric.value
                    if metric.unit == "million":
                        normalized_value = metric.value / 1000
                    
                    company_values.append({
                        "company": company,
                        "value": normalized_value,
                        "unit": "billion",
                        "original_value": metric.value,
                        "original_unit": metric.unit,
                        "filing_date": metric.filing_date
                    })
                
                # Sort by value
                company_values.sort(key=lambda x: x["value"], reverse=True)
                
                comparison["metrics_comparison"][metric_type] = company_values
                comparison["rankings"][metric_type] = [cv["company"] for cv in company_values]
        
        # Generate insights
        comparison["insights"] = self._generate_comparison_insights(comparison)
        
        return comparison
    
    def _generate_comparison_insights(self, comparison: Dict) -> List[str]:
        """Generate insights from revenue comparison"""
        
        insights = []
        
        # Revenue leadership insights
        if "total_revenue" in comparison["rankings"]:
            leader = comparison["rankings"]["total_revenue"][0]
            insights.append(f"{leader} leads in total revenue among compared companies")
        
        # Growth insights
        if "revenue_growth_rate" in comparison["rankings"]:
            growth_leader = comparison["rankings"]["revenue_growth_rate"][0]
            insights.append(f"{growth_leader} shows the highest revenue growth rate")
        
        # Segment insights
        segment_metrics = [k for k in comparison["metrics_comparison"].keys() if "revenue" in k and k not in ["total_revenue", "revenue_growth_rate"]]
        if segment_metrics:
            insights.append(f"Key revenue segments identified: {', '.join(segment_metrics[:3])}")
        
        return insights
    
    def generate_revenue_analysis_report(self, chunks: List) -> Dict:
        """Generate comprehensive revenue analysis report"""
        
        # Extract metrics and drivers
        metrics = self.analyze_revenue_metrics(chunks)
        drivers = self.identify_revenue_drivers(chunks)
        
        # Analyze trends
        trends = self.analyze_revenue_trends(metrics)
        
        # Get unique companies
        companies = list(set(metric.company for metric in metrics))
        
        # Compare across companies
        comparison = self.compare_revenue_across_companies(metrics, companies)
        
        # Generate summary
        report = {
            "summary": {
                "total_companies_analyzed": len(companies),
                "total_revenue_metrics": len(metrics),
                "total_revenue_drivers": len(drivers),
                "analysis_timestamp": self._get_timestamp()
            },
            "companies": companies,
            "revenue_metrics": [self._metric_to_dict(m) for m in metrics],
            "revenue_drivers": [self._driver_to_dict(d) for d in drivers],
            "trend_analysis": trends,
            "cross_company_comparison": comparison,
            "key_insights": self._generate_key_insights(metrics, drivers, trends, comparison)
        }
        
        return report
    
    def _metric_to_dict(self, metric: RevenueMetric) -> Dict:
        """Convert RevenueMetric to dictionary"""
        return {
            "company": metric.company,
            "filing_type": metric.filing_type,
            "filing_date": metric.filing_date,
            "metric_type": metric.metric_type,
            "value": metric.value,
            "unit": metric.unit,
            "context": metric.context,
            "source_section": metric.source_section
        }
    
    def _driver_to_dict(self, driver: RevenueDriver) -> Dict:
        """Convert RevenueDriver to dictionary"""
        return {
            "company": driver.company,
            "driver_type": driver.driver_type,
            "driver_name": driver.driver_name,
            "description": driver.description,
            "importance": driver.importance,
            "trend": driver.trend,
            "source_context": driver.source_context[:200] + "..." if len(driver.source_context) > 200 else driver.source_context
        }
    
    def _generate_key_insights(self, metrics: List[RevenueMetric], drivers: List[RevenueDriver], 
                              trends: Dict, comparison: Dict) -> List[str]:
        """Generate key insights from the analysis"""
        
        insights = []
        
        # Revenue scale insights
        if metrics:
            total_revenue_metrics = [m for m in metrics if m.metric_type == "total_revenue"]
            if total_revenue_metrics:
                max_revenue = max(total_revenue_metrics, key=lambda x: x.value if x.unit == "billion" else x.value/1000)
                insights.append(f"Largest revenue reported: ${max_revenue.value} {max_revenue.unit} by {max_revenue.company}")
        
        # Driver insights
        if drivers:
            # Most common driver types
            driver_types = [d.driver_type for d in drivers]
            most_common_type = max(set(driver_types), key=driver_types.count)
            insights.append(f"Most common revenue driver type: {most_common_type}")
            
            # High importance drivers
            high_importance_drivers = [d for d in drivers if d.importance > 0.7]
            if high_importance_drivers:
                insights.append(f"High-importance revenue drivers identified: {len(high_importance_drivers)}")
        
        # Trend insights
        if trends:
            growing_companies = [company for company, company_trends in trends.items() 
                               if any(trend.get("trend_direction") == "growing" for trend in company_trends.values())]
            if growing_companies:
                insights.append(f"Companies showing revenue growth: {', '.join(growing_companies[:3])}")
        
        return insights
    
    def _initialize_rd_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for R&D spending identification"""
        
        return {
            "rd_expense": [
                r"research\s+and\s+development\s+(?:expenses?|costs?)\s+(?:of\s+|were\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million)",
                r"r&d\s+(?:expenses?|costs?|spending)\s+(?:of\s+|was\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million)",
                r"(?:spent|invested)\s+\$?([\d,]+(?:\.\d+)?)\s*(billion|million)\s+(?:on\s+|in\s+)?(?:research\s+and\s+development|r&d)",
                r"research\s+and\s+development\s+investments?\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million)"
            ],
            "rd_percentage": [
                r"r&d\s+(?:as\s+a\s+percentage\s+of\s+revenue|intensity)\s+(?:of\s+|was\s+)?([\d.]+)%",
                r"research\s+and\s+development\s+(?:as\s+a\s+percentage\s+of\s+revenue|intensity)\s+(?:of\s+)?([\d.]+)%",
                r"([\d.]+)%\s+of\s+revenue\s+(?:on\s+|for\s+)?(?:research\s+and\s+development|r&d)",
                r"invested\s+([\d.]+)%\s+of\s+(?:net\s+)?(?:sales|revenue)\s+in\s+(?:research\s+and\s+development|r&d)"
            ],
            "rd_growth": [
                r"r&d\s+(?:expenses?|spending)\s+(?:increased|grew)\s+(?:by\s+)?([\d.]+)%",
                r"research\s+and\s+development\s+(?:expenses?|spending)\s+(?:increased|grew)\s+(?:by\s+)?([\d.]+)%",
                r"(?:increase|growth)\s+in\s+r&d\s+(?:expenses?|spending)\s+of\s+([\d.]+)%",
                r"([\d.]+)%\s+(?:increase|growth)\s+in\s+(?:research\s+and\s+development|r&d)"
            ]
        }
    
    def _initialize_innovation_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for innovation strategy identification"""
        
        return {
            "technology_focus": [
                r"(?:focus|investment|emphasis)\s+on\s+([a-zA-Z\s]+)\s+(?:technology|technologies|innovation)",
                r"developing\s+(?:new\s+|advanced\s+)?([a-zA-Z\s]+)\s+(?:technologies|capabilities|solutions)",
                r"innovation\s+in\s+([a-zA-Z\s]+)",
                r"technological\s+(?:leadership|advancement)\s+in\s+([a-zA-Z\s]+)"
            ],
            "acquisition": [
                r"acquired\s+([a-zA-Z\s]+)\s+(?:to\s+enhance|for|to\s+expand)",
                r"acquisition\s+of\s+([a-zA-Z\s]+)\s+(?:strengthens|enhances|expands)",
                r"strategic\s+acquisition\s+of\s+([a-zA-Z\s]+)",
                r"purchased\s+([a-zA-Z\s]+)\s+to\s+(?:accelerate|enhance|expand)"
            ],
            "partnership": [
                r"partnership\s+with\s+([a-zA-Z\s]+)\s+(?:to\s+develop|for|to\s+advance)",
                r"collaboration\s+with\s+([a-zA-Z\s]+)\s+(?:on|in|for)",
                r"strategic\s+alliance\s+with\s+([a-zA-Z\s]+)",
                r"joint\s+(?:venture|development)\s+with\s+([a-zA-Z\s]+)"
            ],
            "internal_development": [
                r"internal\s+(?:development|research)\s+(?:of|in)\s+([a-zA-Z\s]+)",
                r"in-house\s+(?:development|innovation)\s+(?:of|in)\s+([a-zA-Z\s]+)",
                r"proprietary\s+([a-zA-Z\s]+)\s+(?:development|technology|platform)",
                r"internally\s+developed\s+([a-zA-Z\s]+)"
            ]
        }
    
    def analyze_rd_spending(self, chunks: List) -> List[RDSpendingMetric]:
        """Extract R&D spending metrics from document chunks"""
        
        rd_metrics = []
        
        for chunk in chunks:
            content = chunk.content
            metadata = chunk.metadata
            
            company = metadata.get('ticker', 'Unknown')
            filing_type = metadata.get('filing_type', 'Unknown')
            filing_date = metadata.get('filing_date', 'Unknown')
            section_type = metadata.get('section_type', 'Unknown')
            
            # Extract different types of R&D metrics
            for metric_type, patterns in self.rd_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        try:
                            if metric_type in ["rd_expense"]:
                                value = float(match.group(1).replace(',', ''))
                                unit = match.group(2).lower()
                                context = match.group(0)
                                
                                rd_metric = RDSpendingMetric(
                                    company=company,
                                    filing_type=filing_type,
                                    filing_date=filing_date,
                                    metric_type=metric_type,
                                    value=value,
                                    unit=unit,
                                    context=context,
                                    source_section=section_type
                                )
                                rd_metrics.append(rd_metric)
                                
                            elif metric_type in ["rd_percentage", "rd_growth"]:
                                value = float(match.group(1))
                                context = match.group(0)
                                
                                rd_metric = RDSpendingMetric(
                                    company=company,
                                    filing_type=filing_type,
                                    filing_date=filing_date,
                                    metric_type=metric_type,
                                    value=value,
                                    unit="percent",
                                    context=context,
                                    source_section=section_type
                                )
                                rd_metrics.append(rd_metric)
                                
                        except (ValueError, IndexError):
                            # Skip invalid matches
                            continue
        
        return rd_metrics
    
    def identify_innovation_strategies(self, chunks: List) -> List[InnovationStrategy]:
        """Identify innovation investment strategies from document chunks"""
        
        strategies = []
        
        for chunk in chunks:
            content = chunk.content
            metadata = chunk.metadata
            
            company = metadata.get('ticker', 'Unknown')
            section_type = metadata.get('section_type', 'Unknown')
            
            # Only analyze relevant sections
            if section_type not in ['management_analysis', 'business', 'financial']:
                continue
            
            # Extract different types of innovation strategies
            for strategy_type, patterns in self.innovation_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        try:
                            strategy_name = match.group(1).strip()
                            
                            # Skip very short or generic names
                            if len(strategy_name) < 3 or strategy_name.lower() in ['the', 'our', 'and', 'or']:
                                continue
                            
                            # Get surrounding context for better analysis
                            start = max(0, match.start() - 150)
                            end = min(len(content), match.end() + 150)
                            context = content[start:end]
                            
                            # Determine investment level and focus areas
                            investment_level = self._analyze_investment_level(context)
                            focus_areas = self._extract_focus_areas(context, strategy_name)
                            
                            strategy = InnovationStrategy(
                                company=company,
                                strategy_type=strategy_type,
                                strategy_name=strategy_name,
                                description=match.group(0),
                                investment_level=investment_level,
                                focus_areas=focus_areas,
                                source_context=context
                            )
                            strategies.append(strategy)
                            
                        except (IndexError, AttributeError):
                            continue
        
        return strategies
    
    def _analyze_investment_level(self, context: str) -> str:
        """Analyze investment level from context"""
        
        context_lower = context.lower()
        
        # High investment indicators
        high_indicators = [
            "significant", "substantial", "major", "large", "massive", "billion",
            "strategic", "critical", "key", "primary", "core", "extensive"
        ]
        
        # Medium investment indicators
        medium_indicators = [
            "moderate", "continued", "ongoing", "regular", "consistent", "million",
            "important", "focused", "targeted", "selective"
        ]
        
        # Low investment indicators
        low_indicators = [
            "limited", "small", "minimal", "reduced", "cautious", "selective",
            "pilot", "experimental", "initial", "exploratory"
        ]
        
        # Count indicators
        high_count = sum(1 for indicator in high_indicators if indicator in context_lower)
        medium_count = sum(1 for indicator in medium_indicators if indicator in context_lower)
        low_count = sum(1 for indicator in low_indicators if indicator in context_lower)
        
        # Determine level based on highest count
        if high_count > medium_count and high_count > low_count:
            return "high"
        elif medium_count > low_count:
            return "medium"
        else:
            return "low"
    
    def _extract_focus_areas(self, context: str, strategy_name: str) -> List[str]:
        """Extract focus areas from context"""
        
        focus_areas = []
        context_lower = context.lower()
        
        # Technology focus areas
        tech_areas = [
            "artificial intelligence", "ai", "machine learning", "cloud computing",
            "cybersecurity", "blockchain", "quantum computing", "5g", "iot",
            "automation", "robotics", "data analytics", "software", "hardware",
            "semiconductors", "biotechnology", "renewable energy", "electric vehicles"
        ]
        
        for area in tech_areas:
            if area in context_lower:
                focus_areas.append(area)
        
        # Also include the strategy name as a focus area if it's technology-related
        if any(tech_word in strategy_name.lower() for tech_word in ["ai", "cloud", "software", "data", "tech"]):
            focus_areas.append(strategy_name.lower())
        
        return list(set(focus_areas))  # Remove duplicates
    
    def analyze_rd_trends(self, rd_metrics: List[RDSpendingMetric]) -> Dict[str, Dict]:
        """Analyze R&D spending trends across companies and time periods"""
        
        trends = defaultdict(lambda: defaultdict(list))
        
        # Group metrics by company and metric type
        for metric in rd_metrics:
            trends[metric.company][metric.metric_type].append(metric)
        
        # Calculate trends for each company
        trend_analysis = {}
        
        for company, company_metrics in trends.items():
            company_trends = {}
            
            for metric_type, metric_list in company_metrics.items():
                # Sort by date
                sorted_metrics = sorted(metric_list, key=lambda x: x.filing_date)
                
                if len(sorted_metrics) >= 2:
                    # Calculate trend
                    first_value = sorted_metrics[0].value
                    last_value = sorted_metrics[-1].value
                    
                    if first_value > 0:
                        growth_rate = ((last_value - first_value) / first_value) * 100
                        
                        company_trends[metric_type] = {
                            "growth_rate": growth_rate,
                            "trend_direction": "growing" if growth_rate > 0 else "declining",
                            "data_points": len(sorted_metrics),
                            "latest_value": last_value,
                            "latest_unit": sorted_metrics[-1].unit,
                            "time_period": f"{sorted_metrics[0].filing_date} to {sorted_metrics[-1].filing_date}"
                        }
            
            trend_analysis[company] = company_trends
        
        return trend_analysis
    
    def compare_rd_across_companies(self, rd_metrics: List[RDSpendingMetric], 
                                   companies: List[str] = None) -> Dict:
        """Compare R&D spending metrics across companies"""
        
        if companies is None:
            companies = list(set(metric.company for metric in rd_metrics))
        
        comparison = {
            "companies": companies,
            "metrics_comparison": {},
            "rankings": {},
            "insights": []
        }
        
        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in rd_metrics:
            if metric.company in companies:
                metrics_by_type[metric.metric_type].append(metric)
        
        # Compare each metric type
        for metric_type, metric_list in metrics_by_type.items():
            # Get latest metric for each company
            latest_metrics = {}
            for metric in metric_list:
                company = metric.company
                if company not in latest_metrics or metric.filing_date > latest_metrics[company].filing_date:
                    latest_metrics[company] = metric
            
            if len(latest_metrics) >= 2:
                # Create comparison
                company_values = []
                for company, metric in latest_metrics.items():
                    # Normalize to billions for expense comparison
                    normalized_value = metric.value
                    if metric_type == "rd_expense" and metric.unit == "million":
                        normalized_value = metric.value / 1000
                    
                    company_values.append({
                        "company": company,
                        "value": normalized_value,
                        "unit": "billion" if metric_type == "rd_expense" else metric.unit,
                        "original_value": metric.value,
                        "original_unit": metric.unit,
                        "filing_date": metric.filing_date
                    })
                
                # Sort by value
                company_values.sort(key=lambda x: x["value"], reverse=True)
                
                comparison["metrics_comparison"][metric_type] = company_values
                comparison["rankings"][metric_type] = [cv["company"] for cv in company_values]
        
        # Generate insights
        comparison["insights"] = self._generate_rd_comparison_insights(comparison)
        
        return comparison
    
    def _generate_rd_comparison_insights(self, comparison: Dict) -> List[str]:
        """Generate insights from R&D comparison"""
        
        insights = []
        
        # R&D spending leadership insights
        if "rd_expense" in comparison["rankings"]:
            leader = comparison["rankings"]["rd_expense"][0]
            insights.append(f"{leader} leads in R&D spending among compared companies")
        
        # R&D intensity insights
        if "rd_percentage" in comparison["rankings"]:
            intensity_leader = comparison["rankings"]["rd_percentage"][0]
            insights.append(f"{intensity_leader} has the highest R&D intensity (% of revenue)")
        
        # R&D growth insights
        if "rd_growth" in comparison["rankings"]:
            growth_leader = comparison["rankings"]["rd_growth"][0]
            insights.append(f"{growth_leader} shows the highest R&D spending growth rate")
        
        return insights
    
    def generate_comprehensive_analysis_report(self, chunks: List) -> Dict:
        """Generate comprehensive revenue and R&D analysis report"""
        
        # Extract all metrics and insights
        revenue_metrics = self.analyze_revenue_metrics(chunks)
        revenue_drivers = self.identify_revenue_drivers(chunks)
        rd_metrics = self.analyze_rd_spending(chunks)
        innovation_strategies = self.identify_innovation_strategies(chunks)
        
        # Analyze trends
        revenue_trends = self.analyze_revenue_trends(revenue_metrics)
        rd_trends = self.analyze_rd_trends(rd_metrics)
        
        # Get unique companies
        companies = list(set(
            list(set(metric.company for metric in revenue_metrics)) +
            list(set(metric.company for metric in rd_metrics))
        ))
        
        # Compare across companies
        revenue_comparison = self.compare_revenue_across_companies(revenue_metrics, companies)
        rd_comparison = self.compare_rd_across_companies(rd_metrics, companies)
        
        # Generate comprehensive report
        report = {
            "summary": {
                "total_companies_analyzed": len(companies),
                "total_revenue_metrics": len(revenue_metrics),
                "total_revenue_drivers": len(revenue_drivers),
                "total_rd_metrics": len(rd_metrics),
                "total_innovation_strategies": len(innovation_strategies),
                "analysis_timestamp": self._get_timestamp()
            },
            "companies": companies,
            "revenue_analysis": {
                "metrics": [self._metric_to_dict(m) for m in revenue_metrics],
                "drivers": [self._driver_to_dict(d) for d in revenue_drivers],
                "trends": revenue_trends,
                "comparison": revenue_comparison
            },
            "rd_analysis": {
                "metrics": [self._rd_metric_to_dict(m) for m in rd_metrics],
                "strategies": [self._strategy_to_dict(s) for s in innovation_strategies],
                "trends": rd_trends,
                "comparison": rd_comparison
            },
            "key_insights": self._generate_comprehensive_insights(
                revenue_metrics, revenue_drivers, rd_metrics, innovation_strategies,
                revenue_trends, rd_trends, revenue_comparison, rd_comparison
            )
        }
        
        return report
    
    def _rd_metric_to_dict(self, metric: RDSpendingMetric) -> Dict:
        """Convert RDSpendingMetric to dictionary"""
        return {
            "company": metric.company,
            "filing_type": metric.filing_type,
            "filing_date": metric.filing_date,
            "metric_type": metric.metric_type,
            "value": metric.value,
            "unit": metric.unit,
            "context": metric.context,
            "source_section": metric.source_section
        }
    
    def _strategy_to_dict(self, strategy: InnovationStrategy) -> Dict:
        """Convert InnovationStrategy to dictionary"""
        return {
            "company": strategy.company,
            "strategy_type": strategy.strategy_type,
            "strategy_name": strategy.strategy_name,
            "description": strategy.description,
            "investment_level": strategy.investment_level,
            "focus_areas": strategy.focus_areas,
            "source_context": strategy.source_context[:200] + "..." if len(strategy.source_context) > 200 else strategy.source_context
        }
    
    def _generate_comprehensive_insights(self, revenue_metrics, revenue_drivers, rd_metrics, 
                                       innovation_strategies, revenue_trends, rd_trends,
                                       revenue_comparison, rd_comparison) -> List[str]:
        """Generate comprehensive insights from all analyses"""
        
        insights = []
        
        # Revenue insights
        if revenue_metrics:
            total_revenue_metrics = [m for m in revenue_metrics if m.metric_type == "total_revenue"]
            if total_revenue_metrics:
                max_revenue = max(total_revenue_metrics, key=lambda x: x.value if x.unit == "billion" else x.value/1000)
                insights.append(f"Largest revenue reported: ${max_revenue.value} {max_revenue.unit} by {max_revenue.company}")
        
        # R&D insights
        if rd_metrics:
            rd_expense_metrics = [m for m in rd_metrics if m.metric_type == "rd_expense"]
            if rd_expense_metrics:
                max_rd = max(rd_expense_metrics, key=lambda x: x.value if x.unit == "billion" else x.value/1000)
                insights.append(f"Highest R&D spending: ${max_rd.value} {max_rd.unit} by {max_rd.company}")
        
        # Innovation strategy insights
        if innovation_strategies:
            strategy_types = [s.strategy_type for s in innovation_strategies]
            most_common_strategy = max(set(strategy_types), key=strategy_types.count)
            insights.append(f"Most common innovation strategy: {most_common_strategy}")
            
            high_investment_strategies = [s for s in innovation_strategies if s.investment_level == "high"]
            if high_investment_strategies:
                insights.append(f"High-investment innovation strategies identified: {len(high_investment_strategies)}")
        
        # Cross-metric insights
        companies_with_both = []
        if revenue_metrics and rd_metrics:
            revenue_companies = set(m.company for m in revenue_metrics)
            rd_companies = set(m.company for m in rd_metrics)
            companies_with_both = list(revenue_companies.intersection(rd_companies))
            
            if companies_with_both:
                insights.append(f"Companies with both revenue and R&D data: {', '.join(companies_with_both[:3])}")
        
        return insights
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()