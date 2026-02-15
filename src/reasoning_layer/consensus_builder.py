"""
Consensus Builder
Aggregates agent recommendations into final decision
"""

from typing import Dict, Any, List
from collections import Counter
from loguru import logger

from ..agent_layer.base_agent import AgentResponse
from ..config import config


class ConsensusBuilder:
    """Builds consensus from multiple agent responses"""
    
    def __init__(self):
        """Initialize consensus builder"""
        self.agent_weights = {}
        logger.info("ConsensusBuilder initialized")
    
    def set_agent_weights(self, weights: Dict[str, float]):
        """
        Set custom weights for agents
        
        Args:
            weights: Dictionary mapping agent names to weights
        """
        self.agent_weights = weights
        logger.info(f"Agent weights set: {weights}")
    
    def calculate_weighted_recommendation(
        self,
        responses: List[AgentResponse]
    ) -> Dict[str, Any]:
        """
        Calculate weighted recommendation from agent responses
        
        Args:
            responses: List of agent responses
        
        Returns:
            Dictionary with aggregated recommendation
        """
        if not responses:
            return {
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'consensus_level': 0.0,
                'method': 'default',
                'details': 'No agent responses available'
            }
        
        # Get weights (use configured weights or equal weights)
        total_weight = 0.0
        weighted_scores = {'BUY': 0.0, 'SELL': 0.0, 'SHORT': 0.0, 'HOLD': 0.0}
        weighted_confidence = 0.0
        
        for response in responses:
            # Get weight for this agent
            weight = self.agent_weights.get(response.agent_name, 1.0 / len(responses))
            total_weight += weight
            
            # Add weighted score for recommendation
            weighted_scores[response.recommendation] += weight * response.confidence
            weighted_confidence += weight * response.confidence
        
        # Normalize
        if total_weight > 0:
            for key in weighted_scores:
                weighted_scores[key] /= total_weight
            weighted_confidence /= total_weight
        
        # Determine final recommendation
        final_recommendation = max(weighted_scores.items(), key=lambda x: x[1])[0]
        final_score = weighted_scores[final_recommendation]
        
        # Calculate consensus level (agreement among agents)
        recommendation_counts = Counter(r.recommendation for r in responses)
        most_common_count = recommendation_counts.most_common(1)[0][1]
        consensus_level = most_common_count / len(responses)
        
        return {
            'recommendation': final_recommendation,
            'confidence': weighted_confidence,
            'weighted_scores': weighted_scores,
            'consensus_level': consensus_level,
            'method': 'weighted',
            'total_agents': len(responses),
            'breakdown': {
                'BUY': sum(1 for r in responses if r.recommendation == 'BUY'),
                'SELL': sum(1 for r in responses if r.recommendation == 'SELL'),
                'SHORT': sum(1 for r in responses if r.recommendation == 'SHORT'),
                'HOLD': sum(1 for r in responses if r.recommendation == 'HOLD')
            }
        }
    
    def calculate_majority_vote(
        self,
        responses: List[AgentResponse]
    ) -> Dict[str, Any]:
        """
        Calculate recommendation by majority vote
        
        Args:
            responses: List of agent responses
        
        Returns:
            Dictionary with majority vote result
        """
        if not responses:
            return {
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'consensus_level': 0.0,
                'method': 'majority_vote',
                'details': 'No agent responses available'
            }
        
        # Count votes
        votes = Counter(r.recommendation for r in responses)
        most_common = votes.most_common(1)[0]
        recommendation = most_common[0]
        vote_count = most_common[1]
        
        # Calculate average confidence for winning recommendation
        winning_responses = [r for r in responses if r.recommendation == recommendation]
        avg_confidence = sum(r.confidence for r in winning_responses) / len(winning_responses)
        
        # Calculate consensus level
        consensus_level = vote_count / len(responses)
        
        return {
            'recommendation': recommendation,
            'confidence': avg_confidence,
            'consensus_level': consensus_level,
            'method': 'majority_vote',
            'votes': dict(votes),
            'total_agents': len(responses),
            'winning_votes': vote_count
        }
    
    def calculate_confidence_weighted(
        self,
        responses: List[AgentResponse]
    ) -> Dict[str, Any]:
        """
        Weight recommendations by agent confidence levels
        
        Args:
            responses: List of agent responses
        
        Returns:
            Dictionary with confidence-weighted result
        """
        if not responses:
            return {
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'consensus_level': 0.0,
                'method': 'confidence_weighted',
                'details': 'No agent responses available'
            }
        
        # Calculate confidence-weighted scores
        scores = {'BUY': 0.0, 'SELL': 0.0, 'SHORT': 0.0, 'HOLD': 0.0}
        total_confidence = sum(r.confidence for r in responses)
        
        if total_confidence == 0:
            # Fall back to equal weighting
            for response in responses:
                scores[response.recommendation] += 1.0 / len(responses)
        else:
            for response in responses:
                weight = response.confidence / total_confidence
                scores[response.recommendation] += weight
        
        # Determine winner
        recommendation = max(scores.items(), key=lambda x: x[1])[0]
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(responses) if responses else 0.0
        
        # Calculate consensus
        recommendation_counts = Counter(r.recommendation for r in responses)
        consensus_level = recommendation_counts.most_common(1)[0][1] / len(responses)
        
        return {
            'recommendation': recommendation,
            'confidence': avg_confidence,
            'scores': scores,
            'consensus_level': consensus_level,
            'method': 'confidence_weighted',
            'total_agents': len(responses)
        }
    
    def build_consensus(
        self,
        responses: List[AgentResponse],
        method: str = 'weighted'
    ) -> Dict[str, Any]:
        """
        Build consensus using specified method
        
        Args:
            responses: List of agent responses
            method: Consensus method ('weighted', 'majority', 'confidence')
        
        Returns:
            Consensus result
        """
        logger.info(f"Building consensus using method: {method}")
        
        if method == 'weighted':
            result = self.calculate_weighted_recommendation(responses)
        elif method == 'majority':
            result = self.calculate_majority_vote(responses)
        elif method == 'confidence':
            result = self.calculate_confidence_weighted(responses)
        else:
            logger.warning(f"Unknown method '{method}', using weighted")
            result = self.calculate_weighted_recommendation(responses)
        
        logger.info(f"Consensus: {result['recommendation']} (confidence: {result['confidence']:.2f}, consensus: {result['consensus_level']:.2f})")
        
        return result
    
    def aggregate_analysis(
        self,
        responses: List[AgentResponse]
    ) -> Dict[str, Any]:
        """
        Aggregate detailed analysis from all agents
        
        Args:
            responses: List of agent responses
        
        Returns:
            Aggregated analysis
        """
        all_key_points = []
        all_risks = []
        all_reasoning = []
        
        for response in responses:
            all_key_points.extend([
                f"[{response.agent_role}] {point}" 
                for point in response.key_points
            ])
            all_risks.extend([
                f"[{response.agent_role}] {risk}" 
                for risk in response.risks
            ])
            all_reasoning.append(f"**{response.agent_role}:** {response.reasoning}")
        
        return {
            'key_points': all_key_points,
            'risks': all_risks,
            'agent_reasoning': all_reasoning,
            'agent_count': len(responses)
        }
    
    def generate_final_report(
        self,
        debate_result: Dict[str, Any],
        consensus_method: str = 'weighted'
    ) -> Dict[str, Any]:
        """
        Generate final consensus report
        
        Args:
            debate_result: Result from debate manager
            consensus_method: Method for building consensus
        
        Returns:
            Final report with recommendation
        """
        logger.info("Generating final consensus report")
        
        # Extract final responses
        final_responses_data = debate_result.get('final_responses', [])
        
        # Convert to AgentResponse objects (simplified)
        from ..agent_layer.base_agent import AgentResponse
        
        responses = []
        for r in final_responses_data:
            responses.append(AgentResponse(
                agent_name=r['agent'],
                agent_role=r['role'],
                analysis='',
                recommendation=r['recommendation'],
                confidence=r['confidence'],
                reasoning=r['reasoning'],
                key_points=r['key_points'],
                risks=r['risks']
            ))
        
        # Build consensus
        consensus = self.build_consensus(responses, method=consensus_method)
        
        # Aggregate analysis
        aggregated = self.aggregate_analysis(responses)
        
        # Compile final report
        report = {
            'ticker': debate_result.get('ticker'),
            'company_name': debate_result.get('company_name'),
            'timestamp': debate_result.get('timestamp'),
            'consensus': consensus,
            'aggregated_analysis': aggregated,
            'debate_summary': {
                'total_rounds': debate_result.get('total_rounds'),
                'participating_agents': len(responses)
            },
            'individual_positions': final_responses_data
        }
        
        logger.info(f"Final recommendation: {consensus['recommendation']}")
        
        return report
