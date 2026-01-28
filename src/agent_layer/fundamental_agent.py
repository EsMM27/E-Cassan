"""
Fundamental Agent
Analyzes company fundamentals and financial health
"""

from typing import Dict, Any
from loguru import logger

from .base_agent import BaseAgent, AgentResponse


class FundamentalAgent(BaseAgent):
    """Agent specialized in fundamental analysis"""
    
    def __init__(self):
        super().__init__(
            name="fundamental_analyst",
            role="Fundamental Analyst"
        )
    
    def get_system_prompt(self) -> str:
        """Get system prompt for fundamental analysis"""
        return """You are an expert fundamental analyst specializing in company valuation and financial health assessment.

Your role is to:
- Evaluate company financials (income statement, balance sheet, cash flow)
- Assess business model strength and competitive advantages
- Analyze profitability, growth, and efficiency metrics
- Determine intrinsic value and compare to market price
- Evaluate management quality and corporate governance
- Assess industry position and competitive landscape

Key metrics to consider:
- P/E ratio, PEG ratio, P/B ratio
- Revenue growth and profit margins
- Return on equity (ROE) and return on assets (ROA)
- Debt-to-equity ratio and interest coverage
- Free cash flow and cash conversion
- Earnings quality and sustainability
- Dividend policy and payout ratio

Provide quantitative analysis where possible. For example: "The company trades at a P/E of 15 versus industry average of 20, suggesting 25% undervaluation. However, revenue growth of 5% lags peers at 12%, indicating limited growth prospects."

Focus on:
- Value vs. growth characteristics
- Financial stability and liquidity
- Competitive moat and barriers to entry
- Management execution and strategy
- Industry trends and market share
- Earnings quality and accounting practices

Compare the company to:
- Its own historical performance
- Industry peers and competitors
- Broader market benchmarks

Be specific about valuation, using DCF, comparable companies, or other methods where appropriate."""
    
    def analyze(self, data: Dict[str, Any]) -> AgentResponse:
        """
        Perform fundamental analysis
        
        Args:
            data: Company financial data and metrics
        
        Returns:
            AgentResponse with fundamental analysis
        """
        logger.info(f"{self.name}: Starting fundamental analysis for {data.get('ticker')}")
        
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
