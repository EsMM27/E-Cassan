"""
Base Agent Class
Abstract base class for all agents in the system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger

from ..config import config


class AgentResponse(BaseModel):
    """Standard response format from agents"""
    agent_name: str
    agent_role: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    analysis: str
    recommendation: str  # BUY, SELL, SHORT, HOLD
    confidence: float = Field(ge=0.0, le=1.0)
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    reasoning: str
    key_points: list[str]
    risks: list[str]
    raw_output: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """Abstract base class for all financial analysis agents"""
    
    def __init__(
        self,
        name: str,
        role: str,
        llm_provider: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """
        Initialize the base agent
        
        Args:
            name: Agent name (e.g., "geopolitical_analyst")
            role: Agent role description
            llm_provider: LLM provider (openai, anthropic, etc.)
            model_name: Specific model to use
        """
        self.name = name
        self.role = role
        
        # Get agent configuration
        agent_config = config.get_agent_config(name)
        self.weight = agent_config.get('weight', 0.25)
        self.description = agent_config.get('description', role)
        
        # LLM configuration - check for agent-specific settings first, then global defaults
        self.llm_provider = llm_provider or agent_config.get('llm_provider') or config.model_config.get('llm', {}).get('default_provider', 'openai')
        self.model_name = model_name or agent_config.get('model_name') or config.model_config.get('llm', {}).get('model_name', 'gpt-4-turbo-preview')
        
        logger.info(f"Initialized {self.name} agent with weight {self.weight}, provider={self.llm_provider}, model={self.model_name}")
    
    def _log_llm_response(self, response: str, ticker: str = "UNKNOWN") -> None:
        """
        Log LLM response to file for inspection
        
        Args:
            response: LLM response text
            ticker: Stock ticker for context
        """
        try:
            from pathlib import Path
            from datetime import datetime
            
            # Create logs/llm_responses directory
            log_dir = Path('logs/llm_responses')
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{ticker}_{self.name}_{timestamp}.txt"
            filepath = log_dir / filename
            
            # Create log content
            log_content = f"""{'=' * 80}
AGENT: {self.name} ({self.role})
PROVIDER: {self.llm_provider}
MODEL: {self.model_name}
TICKER: {ticker}
TIMESTAMP: {timestamp}
{'=' * 80}

{response}

{'=' * 80}
END OF RESPONSE
{'=' * 80}
"""
            
            # Write to file
            filepath.write_text(log_content, encoding='utf-8')
            logger.debug(f"LLM response logged to: {filepath}")
            
        except Exception as e:
            logger.warning(f"Failed to log LLM response: {e}")
    
    @staticmethod
    def describe_time_horizon(months: Optional[int]) -> tuple[str, str]:
        """
        Convert time horizon in months to descriptive categories
        
        Args:
            months: Time horizon in months (1-12) or None
        
        Returns:
            Tuple of (category, description)
        """
        if months is None:
            return "moderate", "a moderate time horizon (3-6 months)"
        elif months <= 3:
            return "short-term", f"a short-term horizon of {months} month{'s' if months > 1 else ''}"
        elif months <= 8:
            return "medium-term", f"a medium-term horizon of {months} months"
        else:
            return "long-term", f"a long-term horizon of {months} months"

    @staticmethod
    def to_optional_float(value: Any) -> Optional[float]:
        """Convert model output to float when possible, else None."""
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any], time_horizon_months: Optional[int] = None) -> AgentResponse:
        """
        Perform analysis on provided data
        
        Args:
            data: Dictionary containing relevant data for analysis
            time_horizon_months: Investment time horizon in months (1-12)
        
        Returns:
            AgentResponse with analysis results
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent
        
        Returns:
            System prompt string
        """
        pass
    
    def format_user_prompt(self, data: Dict[str, Any], time_horizon_months: Optional[int] = None) -> str:
        """
        Format the user prompt with data
        
        Args:
            data: Data to include in prompt
            time_horizon_months: Investment time horizon in months (1-12)
        
        Returns:
            Formatted user prompt
        """
        ticker = data.get('ticker', 'Unknown')
        company_name = data.get('company_name', 'Unknown')
        current_price = data.get('raw_data', {}).get('data', {}).get('stock', {}).get('price_data', {}).get('latest', {}).get('Close')
        if not current_price:
            current_price = data.get('raw_data', {}).get('data', {}).get('stock', {}).get('company_info', {}).get('current_price')
        
        # Get time horizon description
        horizon_category, horizon_description = self.describe_time_horizon(time_horizon_months)
        
        prompt = f"""
Please analyze the following information for {company_name} ({ticker}) with {horizon_description}:

## Stock Information
{data.get('stock_summary', 'No stock data available')}

## Recent News
{data.get('news_summary', 'No news available')}

## Financial Data
{data.get('financial_summary', 'No financial data available')}

## INVESTMENT TIME HORIZON
You are analyzing this stock for {horizon_description.upper()}.
- Short-term (1-3 months): Focus on momentum, technicals, immediate catalysts, and short-term sentiment
- Medium-term (4-8 months): Balance between fundamentals and technical trends, quarterly performance
- Long-term (9-12 months): Emphasize fundamentals, strategic position, competitive advantages, and sustainable growth

Tailor your analysis, recommendation, and confidence level to this specific time horizon.

Based on this information, your role as a {self.role}, and the specified time horizon, provide:
1. A comprehensive analysis
2. Your recommendation (BUY, SELL, SHORT, or HOLD)
3. Your confidence level (0.0 to 1.0)
4. A specific price target (absolute price level)
5. A specific stop loss (absolute price level)
6. Detailed reasoning for your recommendation
7. Key points that support your analysis (list 3-5 points)
8. Potential risks or concerns (list 2-4 risks)

Price level requirements:
- Always provide numeric values for price_target and stop_loss.
- Base levels on the current price context: {current_price if current_price is not None else 'N/A'}
- For BUY: price_target should generally be above current price and stop_loss below.
- For SELL/SHORT: price_target should generally be below current price and stop_loss above.
- For HOLD: provide a neutral range midpoint as price_target and a defensive stop_loss.

Recommendation options:
- BUY: Long position - expect price to rise
- SELL: Exit or avoid - neutral to slightly bearish
- SHORT: Short position - expect price decline
- HOLD: Maintain current position

RESPONSE FORMAT: Return ONLY a valid JSON object (no additional text).

Required JSON structure:
{{
    "analysis": "Your detailed analysis",
    "recommendation": "BUY|SELL|SHORT|HOLD",
    "confidence": 0.75,
    "price_target": 123.45,
    "stop_loss": 110.25,
    "reasoning": "Key reasoning",
    "key_points": ["point 1", "point 2", "point 3"],
    "risks": ["risk 1", "risk 2"]
}}
"""
        return prompt
    
    def call_llm(self, system_prompt: str, user_prompt: str, ticker: str = "UNKNOWN") -> str:
        """
        Call the LLM with prompts and log the response
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            ticker: Stock ticker for logging context
        
        Returns:
            LLM response text
        """
        # Call appropriate provider
        if self.llm_provider == 'openai':
            response = self._call_openai(system_prompt, user_prompt)
        elif self.llm_provider == 'anthropic':
            response = self._call_anthropic(system_prompt, user_prompt)
        elif self.llm_provider == 'ollama':
            response = self._call_ollama(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        
        # Log the response
        self._log_llm_response(response, ticker)
        
        return response
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=config.settings.openai_api_key)
            
            # Try max_completion_tokens first (newer API), fall back to max_tokens
            try:
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=config.model_config.get('llm', {}).get('temperature', 0.7),
                    max_completion_tokens=config.model_config.get('llm', {}).get('max_tokens', 2000)
                )
            except TypeError:
                # Fall back to max_tokens for older OpenAI library versions
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=config.model_config.get('llm', {}).get('temperature', 0.7),
                    max_tokens=config.model_config.get('llm', {}).get('max_tokens', 2000)
                )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise
    
    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic Claude API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=config.settings.anthropic_api_key)
            
            message = client.messages.create(
                model=self.model_name,
                max_tokens=config.model_config.get('llm', {}).get('max_tokens', 2000),
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return message.content[0].text
        
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            raise
    
    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Call local Ollama instance (DeepSeek, Llama, etc.)"""
        try:
            import ollama
            
            ollama_base_url = config.model_config.get('llm', {}).get('ollama_base_url', 'http://localhost:11434')
            
            # Create client with custom base URL if specified
            client = ollama.Client(host=ollama_base_url)
            
            response = client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=False
            )
            
            return response.get('message', {}).get('content', '')
        
        except Exception as e:
            logger.error(f"Error calling Ollama/DeepSeek: {e}")
            raise
    
    def parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM JSON response into structured format
        
        Args:
            response_text: Raw LLM response (expected to contain JSON)
        
        Returns:
            Parsed response dictionary
        """
        import json
        import re
        
        try:
            # Remove thinking tags if present
            cleaned = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
            
            # Extract JSON from markdown code blocks
            code_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
            if code_match:
                return json.loads(code_match.group(1))
            
            # Extract bare JSON object using brace counting
            brace_count = 0
            start_idx = None
            for i, char in enumerate(cleaned):
                if char == '{':
                    if start_idx is None:
                        start_idx = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_idx is not None:
                        return json.loads(cleaned[start_idx:i+1])
            
            # Greedy fallback
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # No JSON found - return safely with defaults
            logger.error(f"No JSON found in response. First 300 chars: {response_text[:300]}")
            return {
                'analysis': response_text[:500],
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'price_target': None,
                'stop_loss': None,
                'reasoning': 'Failed to extract JSON from response',
                'key_points': [],
                'risks': []
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}. Response: {response_text[:300]}")
            return {
                'analysis': response_text[:500],
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'price_target': None,
                'stop_loss': None,
                'reasoning': f'JSON decode error: {str(e)}',
                'key_points': [],
                'risks': []
            }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.role}) - Weight: {self.weight}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', role='{self.role}', weight={self.weight})>"
