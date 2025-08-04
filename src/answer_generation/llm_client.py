import requests
import json
from typing import List, Dict, Optional
import time

from config.settings import (
    LLM_MODEL, MAX_TOKENS, TEMPERATURE, OLLAMA_URL, OLLAMA_MODEL,
    REQUEST_TIMEOUT, MAX_RETRIES, BACKOFF_MAX_TIME
)


class LLMClient:
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model_name = OLLAMA_MODEL
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
        self.request_timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.backoff_max_time = BACKOFF_MAX_TIME
    
    def generate_answer(self, prompt: str, max_retries: int = None) -> Dict:
        if max_retries is None:
            max_retries = self.max_retries
            
        optimized_prompt = self._optimize_prompt(prompt)
        
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": self.model_name,
                    "prompt": optimized_prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                }
                
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer_text = result.get("response", "").strip()
                    
                    if answer_text:
                        return {
                            "answer": answer_text,
                            "model": self.model_name,
                            "tokens_used": 0,
                            "status": "success"
                        }
                    else:
                        return {
                            "answer": "No response generated from the model.",
                            "status": "error",
                            "error": "Empty response"
                        }
                else:
                    print(f"Ollama API error (attempt {attempt + 1}): HTTP {response.status_code}")
                    if attempt == max_retries - 1:
                        return {
                            "answer": "I apologize, but I'm unable to generate an answer due to a technical issue with the local model.",
                            "status": "error",
                            "error": f"HTTP {response.status_code}"
                        }
                
            except requests.exceptions.Timeout:
                print(f"Ollama API timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return {
                        "answer": "I apologize, but the request timed out. Please try again with a shorter query.",
                        "status": "error",
                        "error": "Request timeout"
                    }
                
            except requests.exceptions.ConnectionError:
                print(f"Ollama connection error (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return {
                        "answer": "I apologize, but I cannot connect to the local model server. Please check if Ollama is running.",
                        "status": "error",
                        "error": "Connection error"
                    }
                
            except Exception as e:
                print(f"Ollama API error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return {
                        "answer": "I apologize, but I'm unable to generate an answer due to an unexpected error.",
                        "status": "error",
                        "error": str(e)
                    }
            
            time.sleep(1)
        
        return {
            "answer": "I apologize, but I was unable to generate an answer after multiple attempts.",
            "status": "error",
            "error": "Max retries exceeded"
        }
    
    def _optimize_prompt(self, prompt: str) -> str:
        
        system_instruction = "You are a financial analyst expert in SEC filings analysis. Provide accurate, concise answers with proper source attribution."
        
        if len(prompt) > 8000:
            lines = prompt.split('\n')
            if len(lines) > 20:
                prompt = '\n'.join(lines[:10]) + '\n\n[Additional context truncated for brevity]\n\n' + '\n'.join(lines[-10:])
        
        return f"{system_instruction}\n\n{prompt}"
    
    def _calculate_backoff_time(self, attempt: int) -> int:
        
        import random
        
        base_wait = (2 ** (attempt + 1)) - 2
        jitter = random.uniform(0.5, 1.5)
        
        return min(int(base_wait * jitter), self.backoff_max_time)
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        
        prompt = f"""
        Please provide a concise summary of the following text in no more than {max_length} words:
        
        {text}
        
        Summary:
        """
        
        result = self.generate_answer(prompt)
        return result.get("answer", "Unable to generate summary")
    
    def extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        
        prompt = f"""
        Extract the {num_points} most important key points from the following text:
        
        {text}
        
        Please format as a numbered list:
        """
        
        result = self.generate_answer(prompt)
        answer = result.get("answer", "")
        
        points = []
        for line in answer.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                clean_point = line.split('.', 1)[-1].strip()
                if clean_point:
                    points.append(clean_point)
        
        return points[:num_points]
    
    def check_factual_consistency(self, answer: str, source_text: str) -> Dict:
        
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
        
        response = result.get("answer", "")
        
        score = 5
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