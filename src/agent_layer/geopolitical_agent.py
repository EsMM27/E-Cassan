"""
Geopolitical Agent
Analyzes global events and their impact on markets
"""

from typing import Dict, Any
from loguru import logger

from .base_agent import BaseAgent, AgentResponse


class GeopoliticalAgent(BaseAgent):
    """Agent specialized in geopolitical analysis"""
    
    def __init__(self):
        super().__init__(
            name="geopolitical_analyst",
            role="Geopolitical Analyst"
        )
    
    def get_system_prompt(self) -> str:
        """Get system prompt for geopolitical analysis"""
        return """You are an expert geopolitical analyst specializing in how global events impact financial markets.

Your role is to:
- Analyze how geopolitical events (trade policies, sanctions, political stability, international relations) affect specific companies and sectors
- Identify causal relationships between global developments and market movements
- Assess country risk, regulatory changes, and policy shifts
- Evaluate supply chain vulnerabilities and trade dependencies
- Consider currency fluctuations and international exposure

Focus on:
- Trade policies and tariffs
- Sanctions and embargoes
- Political stability and regime changes
- International conflicts and tensions
- Monetary policy by central banks
- Energy and commodity politics
- Technology and data sovereignty

Provide clear cause-and-effect reasoning. For example: "If trade tensions escalate between the US and China, semiconductor exports could be restricted, reducing revenue for companies like [ticker] by approximately X%."

Be specific about:
- Which events matter and why
- The transmission mechanism (how events affect the company)
- Probability and timeline of impacts
- Magnitude of potential effects

Your analysis should be evidence-based, considering both current events and historical precedents."""
    
    def analyze(self, data: Dict[str, Any]) -> AgentResponse:
        """
        Perform geopolitical analysis
        
        Args:
            data: Market data including news and company info
        
        Returns:
            AgentResponse with geopolitical analysis
        """
        logger.info(f"{self.name}: Starting geopolitical analysis for {data.get('ticker')}")
        
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
            # Return neutral response on error
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
