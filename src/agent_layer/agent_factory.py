"""
Agent Factory
Creates and manages agent instances
"""

from typing import Dict, List, Optional
from loguru import logger

from .base_agent import BaseAgent
from .geopolitical_agent import GeopoliticalAgent
from .fundamental_agent import FundamentalAgent
from .technical_agent import TechnicalAgent
from .sentiment_agent import SentimentAgent


class AgentFactory:
    """Factory for creating and managing agents"""
    
    @staticmethod
    def create_agent(agent_type: str, **kwargs) -> BaseAgent:
        """
        Create an agent of specified type
        
        Args:
            agent_type: Type of agent to create
            **kwargs: Additional arguments for agent initialization
        
        Returns:
            Agent instance
        """
        agent_map = {
            'geopolitical': GeopoliticalAgent,
            'geopolitical_analyst': GeopoliticalAgent,
            'fundamental': FundamentalAgent,
            'fundamental_analyst': FundamentalAgent,
            'technical': TechnicalAgent,
            'technical_analyst': TechnicalAgent,
            'sentiment': SentimentAgent,
            'sentiment_analyst': SentimentAgent,
        }
        
        agent_class = agent_map.get(agent_type.lower())
        
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        logger.info(f"Creating agent: {agent_type}")
        return agent_class(**kwargs)
    
    @staticmethod
    def create_all_agents() -> List[BaseAgent]:
        """
        Create all available agents
        
        Returns:
            List of all agent instances
        """
        logger.info("Creating all agents")
        
        agents = [
            GeopoliticalAgent(),
            FundamentalAgent(),
            TechnicalAgent(),
            SentimentAgent()
        ]
        
        logger.info(f"Created {len(agents)} agents")
        return agents
    
    @staticmethod
    def get_agent_weights(agents: List[BaseAgent]) -> Dict[str, float]:
        """
        Get weight configuration for all agents
        
        Args:
            agents: List of agent instances
        
        Returns:
            Dictionary mapping agent names to weights
        """
        return {agent.name: agent.weight for agent in agents}
