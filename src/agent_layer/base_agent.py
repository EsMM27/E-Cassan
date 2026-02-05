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
    recommendation: str  # BUY, SELL, HOLD
    confidence: float = Field(ge=0.0, le=1.0)
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
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> AgentResponse:
        """
        Perform analysis on provided data
        
        Args:
            data: Dictionary containing relevant data for analysis
        
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
    
    def format_user_prompt(self, data: Dict[str, Any]) -> str:
        """
        Format the user prompt with data
        
        Args:
            data: Data to include in prompt
        
        Returns:
            Formatted user prompt
        """
        ticker = data.get('ticker', 'Unknown')
        company_name = data.get('company_name', 'Unknown')
        
        prompt = f"""
Please analyze the following information for {company_name} ({ticker}):

## Stock Information
{data.get('stock_summary', 'No stock data available')}

## Recent News
{data.get('news_summary', 'No news available')}

## Financial Data
{data.get('financial_summary', 'No financial data available')}

Based on this information and your role as a {self.role}, provide:
1. A comprehensive analysis
2. Your recommendation (BUY, SELL, or HOLD)
3. Your confidence level (0.0 to 1.0)
4. Detailed reasoning for your recommendation
5. Key points that support your analysis (list 3-5 points)
6. Potential risks or concerns (list 2-4 risks)

Format your response as JSON with the following structure:
{{
    "analysis": "Your detailed analysis here",
    "recommendation": "BUY|SELL|HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed reasoning for your recommendation",
    "key_points": ["point 1", "point 2", ...],
    "risks": ["risk 1", "risk 2", ...]
}}
"""
        return prompt
    
    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call the LLM with prompts
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
        
        Returns:
            LLM response text
        """
        # This is a placeholder - implement actual LLM calls
        if self.llm_provider == 'openai':
            return self._call_openai(system_prompt, user_prompt)
        elif self.llm_provider == 'anthropic':
            return self._call_anthropic(system_prompt, user_prompt)
        elif self.llm_provider == 'ollama':
            return self._call_ollama(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
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
        Parse LLM response into structured format
        
        Args:
            response_text: Raw LLM response
        
        Returns:
            Parsed response dictionary
        """
        import json
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # If no JSON found, return raw text
                return {
                    'analysis': response_text,
                    'recommendation': 'HOLD',
                    'confidence': 0.5,
                    'reasoning': 'Unable to parse structured response',
                    'key_points': [],
                    'risks': []
                }
        
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON")
            return {
                'analysis': response_text,
                'recommendation': 'HOLD',
                'confidence': 0.5,
                'reasoning': 'Unable to parse structured response',
                'key_points': [],
                'risks': []
            }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.role}) - Weight: {self.weight}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', role='{self.role}', weight={self.weight})>"
