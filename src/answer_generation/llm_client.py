import google.generativeai as genai
from typing import List, Dict, Optional
import time

from config.settings import GEMINI_API_KEY, LLM_MODEL, MAX_TOKENS, TEMPERATURE


class LLMClient:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model_name = LLM_MODEL
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
    
    def generate_answer(self, prompt: str, max_retries: int = 3) -> Dict:
        """Generate answer using Gemini API."""
        
        # Add system instruction to prompt
        full_prompt = f"You are a financial analyst expert in SEC filings analysis.\n\n{prompt}"
        
        for attempt in range(max_retries):
            try:
                response = genai.generate_text(
                    model=self.model_name,
                    prompt=full_prompt,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
                
                return {
                    "answer": response.result if response.result else "No response generated",
                    "model": self.model_name,
                    "tokens_used": 0,  # Token count not available in this version
                    "status": "success"
                }
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Handle rate limiting
                if "quota" in error_msg or "rate" in error_msg:
                    wait_time = (2 ** attempt) * 1
                    print(f"Rate limit hit, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                print(f"Gemini API error: {e}")
                if attempt == max_retries - 1:
                    return {
                        "answer": "I apologize, but I'm unable to generate an answer due to a technical issue.",
                        "status": "error",
                        "error": str(e)
                    }
        
        return {
            "answer": "I apologize, but I was unable to generate an answer after multiple attempts.",
            "status": "error",
            "error": "Max retries exceeded"
        }
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a summary of the given text."""
        
        prompt = f"""
        Please provide a concise summary of the following text in no more than {max_length} words:
        
        {text}
        
        Summary:
        """
        
        result = self.generate_answer(prompt)
        return result.get("answer", "Unable to generate summary")
    
    def extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """Extract key points from text."""
        
        prompt = f"""
        Extract the {num_points} most important key points from the following text:
        
        {text}
        
        Please format as a numbered list:
        """
        
        result = self.generate_answer(prompt)
        answer = result.get("answer", "")
        
        # Parse numbered list
        points = []
        for line in answer.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering and clean up
                clean_point = line.split('.', 1)[-1].strip()
                if clean_point:
                    points.append(clean_point)
        
        return points[:num_points]
    
    def check_factual_consistency(self, answer: str, source_text: str) -> Dict:
        """Check if answer is consistent with source text."""
        
        prompt = f"""
        Please evaluate if the following answer is factually consistent with the provided source text.
        
        Source Text:
        {source_text}
        
        Answer to Evaluate:
        {answer}
        
        Please respond with:
        1. Consistency Score (1-10, where 10 is perfectly consistent)
        2. Any factual inconsistencies found
        3. Overall assessment
        """
        
        result = self.generate_answer(prompt)
        
        # Simple parsing of consistency check
        response = result.get("answer", "")
        
        # Extract score (basic pattern matching)
        score = 5  # Default
        if "Score:" in response or "score" in response.lower():
            import re
            score_match = re.search(r'(\d+)', response)
            if score_match:
                score = min(10, max(1, int(score_match.group(1))))
        
        return {
            "consistency_score": score,
            "detailed_assessment": response,
            "is_consistent": score >= 7
        }