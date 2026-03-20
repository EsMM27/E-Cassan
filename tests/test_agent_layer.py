"""
Tests for Agent Layer
"""

import pytest
from src.agent_layer.base_agent import AgentResponse
from src.agent_layer.agent_factory import AgentFactory


class TestAgentFactory:
    """Tests for AgentFactory"""
    
    def test_create_geopolitical_agent(self):
        """Test creating geopolitical agent"""
        agent = AgentFactory.create_agent('geopolitical')
        
        assert agent.name == 'geopolitical_analyst'
        assert agent.role == 'Geopolitical Analyst'
        assert agent.weight > 0
    
    def test_create_fundamental_agent(self):
        """Test creating fundamental agent"""
        agent = AgentFactory.create_agent('fundamental')
        
        assert agent.name == 'fundamental_analyst'
        assert agent.role == 'Fundamental Analyst'
    
    def test_create_all_agents(self):
        """Test creating all agents"""
        agents = AgentFactory.create_all_agents()
        
        assert len(agents) == 4
        agent_names = [a.name for a in agents]
        assert 'geopolitical_analyst' in agent_names
        assert 'fundamental_analyst' in agent_names
        assert 'technical_analyst' in agent_names
        assert 'sentiment_analyst' in agent_names
    
    def test_get_agent_weights(self):
        """Test getting agent weights"""
        agents = AgentFactory.create_all_agents()
        weights = AgentFactory.get_agent_weights(agents)
        
        assert len(weights) == 4
        assert all(0 < w <= 1 for w in weights.values())


class TestAgentResponse:
    """Tests for AgentResponse"""
    
    def test_agent_response_creation(self):
        """Test creating agent response"""
        response = AgentResponse(
            agent_name='test_agent',
            agent_role='Test Role',
            analysis='Test analysis',
            recommendation='BUY',
            confidence=0.8,
            reasoning='Test reasoning',
            key_points=['Point 1'],
            risks=['Risk 1']
        )
        
        assert response.agent_name == 'test_agent'
        assert response.recommendation == 'BUY'
        assert response.confidence == 0.8
    
    def test_agent_response_validation(self):
        """Test response validation"""
        # Confidence must be between 0 and 1
        with pytest.raises(ValueError):
            AgentResponse(
                agent_name='test',
                agent_role='Test',
                analysis='Test',
                recommendation='BUY',
                confidence=1.5,  # Invalid
                reasoning='Test',
                key_points=[],
                risks=[]
            )
