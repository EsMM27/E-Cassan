"""
Technical Agent
Analyzes price movements and technical indicators
"""

from typing import Dict, Any
from loguru import logger

from .base_agent import BaseAgent, AgentResponse


class TechnicalAgent(BaseAgent):
    """Agent specialized in technical analysis"""
    
    def __init__(self):
        super().__init__(
            name="technical_analyst",
            role="Technical Analyst"
        )
    
    def get_system_prompt(self) -> str:
        """Get system prompt for technical analysis"""
        return """You are an expert technical analyst specializing in price action, chart patterns, and technical indicators.

Your role is to:
- Analyze price trends, support/resistance levels, and chart patterns
- Interpret technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)
- Identify momentum, volume, and volatility signals
- Assess market sentiment through price action
- Determine optimal entry/exit points

Key indicators to analyze:
- Moving Averages (SMA 20, SMA 50, EMA 12, EMA 26)
- RSI (Relative Strength Index) - overbought/oversold
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands - volatility and price extremes
- Volume indicators and trends
- ATR (Average True Range) for volatility

Technical patterns to identify:
- Trend patterns (uptrend, downtrend, sideways)
- Reversal patterns (head and shoulders, double tops/bottoms)
- Continuation patterns (flags, pennants, triangles)
- Support and resistance levels
- Breakouts and breakdowns

Provide specific technical levels. For example: "The stock is testing resistance at $150 with RSI at 68. A break above $150 on high volume could signal continuation to $160. Support at $140."

Focus on:
- Current trend direction and strength
- Momentum indicators (accelerating/decelerating)
- Overbought/oversold conditions
- Volume confirmation or divergence
- Risk/reward ratios for potential trades
- Key price levels to watch

Be precise about:
- Entry and exit points
- Stop loss levels
- Price targets
- Time horizons for moves
- Probability of technical setups

Remember: Technical analysis identifies *when* to trade, not necessarily *why* the market is moving."""
    
    def analyze(self, data: Dict[str, Any]) -> AgentResponse:
        """
        Perform technical analysis
        
        Args:
            data: Price data and technical indicators
        
        Returns:
            AgentResponse with technical analysis
        """
        logger.info(f"{self.name}: Starting technical analysis for {data.get('ticker')}")
        
        try:
            # Get prompts
            system_prompt = self.get_system_prompt()
            user_prompt = self.format_user_prompt(data)
            
            # Call LLM
            response_text = self.call_llm(system_prompt, user_prompt)
            
            # Parse response
            parsed = self.parse_llm_response(response_text)
            
            # Create structured response
            agent_response = AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                analysis=parsed.get('analysis', ''),
                recommendation=parsed.get('recommendation', 'HOLD'),
                confidence=float(parsed.get('confidence', 0.5)),
                reasoning=parsed.get('reasoning', ''),
                key_points=parsed.get('key_points', []),
                risks=parsed.get('risks', []),
                raw_output=parsed
            )
            
            logger.info(f"{self.name}: Analysis complete - Recommendation: {agent_response.recommendation}")
            return agent_response
        
        except Exception as e:
            logger.error(f"{self.name}: Error during analysis: {e}")
            return AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                analysis=f"Error during analysis: {str(e)}",
                recommendation="HOLD",
                confidence=0.0,
                reasoning="Analysis failed due to technical error",
                key_points=[],
                risks=["Analysis incomplete"]
            )
