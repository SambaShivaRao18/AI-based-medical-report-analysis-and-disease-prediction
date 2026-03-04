import groq
import os
import time
from typing import Dict, Any, Optional

class ModelManager:
    """
    Manages AI model selection and Groq API communication with fallback logic.
    Uses currently supported Groq models for robust analysis.
    """
    
    # Updated list of supported models with a fallback hierarchy
    MODEL_CONFIG = [
        # Primary: High-tier model for comprehensive analysis
        {"provider": "groq", "model": "llama-3.1-70b-versatile", "max_tokens": 3000, "temperature": 0.7},
        # Secondary: Mid-tier model for good performance/cost balance
        {"provider": "groq", "model": "mixtral-8x22b-32768", "max_tokens": 3000, "temperature": 0.7},
        # Tertiary: Fast, low-cost model as a reliable fallback
        {"provider": "groq", "model": "llama-3.1-8b-instant", "max_tokens": 3000, "temperature": 0.7}
    ]
    
    def __init__(self):
        # API key is read from environment variable for security
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            # Note: This error is caught in app.py for graceful startup failure
            raise ValueError("GROQ_API_KEY environment variable not set.")
        self.client = groq.Groq(api_key=self.api_key)

    def generate_analysis(self, data: Dict[str, str], system_prompt: str) -> Dict[str, Any]:
        """
        Generate analysis using the first available model with automatic fallback.
        
        Args:
            data: Report data to analyze.
            system_prompt: Base system prompt.
        """
        for config in self.MODEL_CONFIG:
            model = config["model"]
            try:
                print(f"Attempting generation with model: {model}") # For Flask console debugging
                
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": str(data)}
                    ],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"]
                )
                
                return {
                    "success": True,
                    "content": completion.choices[0].message.content,
                    "model_used": model
                }
                
            except Exception as e:
                error_message = str(e).lower()
                print(f"Model {model} failed: {error_message}")
                
                # Wait briefly before trying the next model
                time.sleep(1) 
                
                # If it's a model decommission error or rate limit, the loop will continue to the next fallback model.
                continue
            
        return {"success": False, "error": "Analysis failed with all available AI models. Please check your Groq API key and rate limits."}