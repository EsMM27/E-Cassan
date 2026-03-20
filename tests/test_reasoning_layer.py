"""
Tests for Reasoning Layer
"""

import pytest
from src.reasoning_layer.reasoning_logger import ReasoningLogger
from src.reasoning_layer.consensus_builder import ConsensusBuilder
from src.agent_layer.base_agent import AgentResponse


class TestConsensusBuilder:
    """Tests for ConsensusBuilder"""
    
    def test_majority_vote(self):
        """Test majority vote consensus"""
        builder = ConsensusBuilder()
        
        responses = [
            AgentResponse(
                agent_name='agent1', agent_role='Role1',
                analysis='', recommendation='BUY', confidence=0.8,
                price_target=110.0, stop_loss=95.0,
                reasoning='', key_points=[], risks=[]
            ),
            AgentResponse(
                agent_name='agent2', agent_role='Role2',
                analysis='', recommendation='BUY', confidence=0.7,
                price_target=112.0, stop_loss=96.0,
                reasoning='', key_points=[], risks=[]
            ),
            AgentResponse(
                agent_name='agent3', agent_role='Role3',
                analysis='', recommendation='HOLD', confidence=0.6,
                price_target=100.0, stop_loss=90.0,
                reasoning='', key_points=[], risks=[]
            )
        ]
        
        result = builder.calculate_majority_vote(responses)
        
        assert result['recommendation'] == 'BUY'
        assert result['consensus_level'] == 2/3
        assert result['method'] == 'majority_vote'
    
    def test_weighted_recommendation(self):
        """Test weighted recommendation"""
        builder = ConsensusBuilder()
        builder.set_agent_weights({
            'agent1': 0.4,
            'agent2': 0.3,
            'agent3': 0.3
        })
        
        responses = [
            AgentResponse(
                agent_name='agent1', agent_role='Role1',
                analysis='', recommendation='BUY', confidence=0.9,
                price_target=120.0, stop_loss=98.0,
                reasoning='', key_points=[], risks=[]
            ),
            AgentResponse(
                agent_name='agent2', agent_role='Role2',
                analysis='', recommendation='SELL', confidence=0.8,
                price_target=90.0, stop_loss=105.0,
                reasoning='', key_points=[], risks=[]
            ),
            AgentResponse(
                agent_name='agent3', agent_role='Role3',
                analysis='', recommendation='HOLD', confidence=0.5,
                price_target=100.0, stop_loss=92.0,
                reasoning='', key_points=[], risks=[]
            )
        ]
        
        result = builder.calculate_weighted_recommendation(responses)
        
        assert result['recommendation'] in ['BUY', 'SELL', 'HOLD']
        assert 0 <= result['confidence'] <= 1
        assert result['method'] == 'weighted'

    def test_aggregate_price_levels(self):
        """Test consensus price target/stop loss aggregation"""
        builder = ConsensusBuilder()
        builder.set_agent_weights({'agent1': 0.6, 'agent2': 0.4})

        responses = [
            AgentResponse(
                agent_name='agent1', agent_role='Role1',
                analysis='', recommendation='BUY', confidence=0.9,
                price_target=120.0, stop_loss=96.0,
                reasoning='', key_points=[], risks=[]
            ),
            AgentResponse(
                agent_name='agent2', agent_role='Role2',
                analysis='', recommendation='BUY', confidence=0.7,
                price_target=110.0, stop_loss=94.0,
                reasoning='', key_points=[], risks=[]
            )
        ]

        aggregated = builder.aggregate_price_levels(responses, final_recommendation='BUY')

        assert aggregated['price_target'] is not None
        assert aggregated['stop_loss'] is not None
        assert aggregated['price_target'] > 110.0
        assert aggregated['contributors'] == 2
    
    def test_aggregate_analysis(self):
        """Test analysis aggregation"""
        builder = ConsensusBuilder()
        
        responses = [
            AgentResponse(
                agent_name='agent1', agent_role='Analyst1',
                analysis='', recommendation='BUY', confidence=0.8,
                price_target=111.0, stop_loss=95.0,
                reasoning='Strong fundamentals',
                key_points=['Point 1', 'Point 2'],
                risks=['Risk 1']
            ),
            AgentResponse(
                agent_name='agent2', agent_role='Analyst2',
                analysis='', recommendation='BUY', confidence=0.7,
                price_target=112.0, stop_loss=96.0,
                reasoning='Positive sentiment',
                key_points=['Point 3'],
                risks=['Risk 2', 'Risk 3']
            )
        ]
        
        aggregated = builder.aggregate_analysis(responses)
        
        assert len(aggregated['key_points']) == 3
        assert len(aggregated['risks']) == 3
        assert aggregated['agent_count'] == 2


class TestReasoningLogger:
    """Tests for ReasoningLogger"""

    def test_log_debate_writes_json_audit_file(self, tmp_path):
        """Test debate audit JSON is written to reasoning log directory"""
        logger = ReasoningLogger(log_dir=str(tmp_path))

        debate_result = {
            'ticker': 'TEST',
            'company_name': 'Test Company',
            'timestamp': '2026-03-20T10:00:00',
            'total_rounds': 1,
            'rounds': [],
            'final_responses': []
        }

        log_path = logger.log_debate(debate_result)

        assert log_path.exists()
        assert log_path.suffix == '.json'

        content = log_path.read_text(encoding='utf-8')
        assert '"ticker": "TEST"' in content
