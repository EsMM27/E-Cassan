"""
Debate Manager
Orchestrates debate between agents
"""

from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from ..agent_layer.base_agent import BaseAgent, AgentResponse
from ..config import config
from .reasoning_logger import ReasoningLogger


class DebateRound:
    """Represents a single round of debate"""
    
    def __init__(self, round_number: int):
        self.round_number = round_number
        self.agent_responses: List[AgentResponse] = []
        self.debates: List[Dict[str, Any]] = []
        self.consensus_level: float = 0.0
        self.timestamp = datetime.now().isoformat()
    
    def add_response(self, response: AgentResponse):
        """Add an agent response to this round"""
        self.agent_responses.append(response)
    
    def add_debate(self, debate: Dict[str, Any]):
        """Add a debate exchange to this round"""
        self.debates.append(debate)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'round_number': self.round_number,
            'timestamp': self.timestamp,
            'consensus_level': self.consensus_level,
            'agent_responses': [
                {
                    'agent': r.agent_name,
                    'recommendation': r.recommendation,
                    'confidence': r.confidence,
                    'reasoning': r.reasoning,
                    'key_points': r.key_points,
                    'risks': r.risks
                }
                for r in self.agent_responses
            ],
            'debates': self.debates
        }


class DebateManager:
    """Manages debate process between agents"""
    
    def __init__(self, agents: List[BaseAgent], logger_instance: ReasoningLogger = None):
        """
        Initialize debate manager
        
        Args:
            agents: List of agent instances
            logger_instance: Optional reasoning logger
        """
        self.agents = agents
        self.reasoning_logger = logger_instance or ReasoningLogger()
        
        # Get configuration
        self.max_rounds = config.reasoning_config.get('max_debate_rounds', 3)
        self.consensus_threshold = config.reasoning_config.get('consensus_threshold', 0.75)
        self.enable_logging = config.reasoning_config.get('enable_logging', True)
        
        logger.info(f"DebateManager initialized with {len(agents)} agents")
        logger.info(f"Max debate rounds: {self.max_rounds}, Consensus threshold: {self.consensus_threshold}")
    
    def calculate_consensus(self, responses: List[AgentResponse]) -> float:
        """
        Calculate consensus level among agents
        
        Args:
            responses: Agent responses
        
        Returns:
            Consensus level (0.0 to 1.0)
        """
        if not responses:
            return 0.0
        
        # Count recommendations
        recommendations = [r.recommendation for r in responses]
        most_common = max(set(recommendations), key=recommendations.count)
        agreement_count = recommendations.count(most_common)
        
        return agreement_count / len(responses)
    
    def conduct_initial_analysis(self, data: Dict[str, Any]) -> List[AgentResponse]:
        """
        Conduct initial analysis by all agents independently
        
        Args:
            data: Formatted data for analysis
        
        Returns:
            List of agent responses
        """
        logger.info("=== Starting Initial Analysis Phase ===")
        
        responses = []
        for agent in self.agents:
            try:
                logger.info(f"Agent {agent.name} performing analysis...")
                response = agent.analyze(data)
                responses.append(response)
                logger.info(f"Agent {agent.name} completed: {response.recommendation} (confidence: {response.confidence:.2f})")
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")
        
        logger.info(f"=== Initial Analysis Complete: {len(responses)}/{len(self.agents)} agents responded ===")
        return responses
    
    def identify_disagreements(self, responses: List[AgentResponse]) -> List[Dict[str, Any]]:
        """
        Identify key disagreements between agents
        
        Args:
            responses: List of agent responses
        
        Returns:
            List of disagreement points
        """
        disagreements = []
        
        # Group by recommendation
        buy_agents = [r for r in responses if r.recommendation == 'BUY']
        sell_agents = [r for r in responses if r.recommendation == 'SELL']
        short_agents = [r for r in responses if r.recommendation == 'SHORT']
        hold_agents = [r for r in responses if r.recommendation == 'HOLD']
        
        # Check for conflicting recommendations
        if len(buy_agents) > 0 and (len(sell_agents) > 0 or len(short_agents) > 0):
            description = f"{len(buy_agents)} agents recommend BUY while "
            if len(sell_agents) > 0 and len(short_agents) > 0:
                description += f"{len(sell_agents)} recommend SELL and {len(short_agents)} recommend SHORT"
            elif len(sell_agents) > 0:
                description += f"{len(sell_agents)} recommend SELL"
            else:
                description += f"{len(short_agents)} recommend SHORT"
            
            disagreements.append({
                'type': 'recommendation_conflict',
                'description': description,
                'buy_agents': [a.agent_name for a in buy_agents],
                'sell_agents': [a.agent_name for a in sell_agents],
                'short_agents': [a.agent_name for a in short_agents]
            })
        
        # Check for confidence spread
        if responses:
            confidences = [r.confidence for r in responses]
            confidence_spread = max(confidences) - min(confidences)
            
            if confidence_spread > 0.4:
                disagreements.append({
                    'type': 'confidence_divergence',
                    'description': f"High confidence spread: {confidence_spread:.2f}",
                    'high_confidence': [r.agent_name for r in responses if r.confidence > 0.7],
                    'low_confidence': [r.agent_name for r in responses if r.confidence < 0.4]
                })
        
        return disagreements
    
    def generate_debate_prompt(
        self,
        responses: List[AgentResponse],
        disagreements: List[Dict[str, Any]],
        round_number: int
    ) -> str:
        """
        Generate prompt for debate round
        
        Args:
            responses: Current agent responses
            disagreements: Identified disagreements
            round_number: Current debate round
        
        Returns:
            Debate prompt string
        """
        prompt = f"""
# Multi-Agent Debate - Round {round_number}

## Current Positions

"""
        for response in responses:
            prompt += f"""
### {response.agent_role} ({response.agent_name})
- **Recommendation:** {response.recommendation}
- **Confidence:** {response.confidence:.2f}
- **Key Reasoning:** {response.reasoning[:200]}...
- **Main Points:**
"""
            for point in response.key_points[:3]:
                prompt += f"  - {point}\n"
        
        if disagreements:
            prompt += "\n## Key Disagreements\n"
            for disagreement in disagreements:
                prompt += f"- {disagreement['description']}\n"
        
        prompt += """

## Debate Instructions

Each agent should:
1. Review other agents' analyses and identify points of agreement/disagreement
2. Defend your position with specific evidence
3. Challenge weak arguments from other agents with counterpoints
4. Be open to adjusting your recommendation if compelling evidence is presented
5. Focus on causal relationships, not just correlations

**CRITICAL: Sentiment Validation**
All agents MUST cross-check Sentiment Agent's analysis:
- Does news optimism/pessimism match ACTUAL financial performance?
- Example: If sentiment is 80% positive, verify revenue/profit growth justifies it
- Example: If sentiment is 70% negative, check if fundamentals really deteriorated
- Red flag: High sentiment + weak fundamentals = HYPE (discount sentiment)
- Red flag: Low sentiment + strong fundamentals = FUD (contrarian opportunity)

Fundamental/Technical agents: You have hard data - challenge sentiment if it's detached from reality.

Respond with:
- Your updated recommendation (BUY/SELL/SHORT/HOLD)
- Your updated confidence (0.0-1.0)
- Specific rebuttals to arguments you disagree with (especially sentiment claims)
- New evidence that supports your position
- Any concessions you're willing to make

Format as JSON:
{
    "recommendation": "BUY|SELL|SHORT|HOLD",
    "confidence": 0.0-1.0,
    "rebuttals": ["rebuttal 1", "rebuttal 2"],
    "supporting_evidence": ["evidence 1", "evidence 2"],
    "concessions": ["concession 1", "concession 2"]
}
"""
        return prompt
    
    def conduct_debate_round(
        self,
        data: Dict[str, Any],
        previous_responses: List[AgentResponse],
        round_number: int
    ) -> DebateRound:
        """
        Conduct one round of debate
        
        Args:
            data: Original data
            previous_responses: Responses from previous round
            round_number: Current round number
        
        Returns:
            DebateRound object with results
        """
        logger.info(f"=== Starting Debate Round {round_number} ===")
        
        debate_round = DebateRound(round_number)
        
        # Identify disagreements
        disagreements = self.identify_disagreements(previous_responses)
        
        if not disagreements:
            logger.info("No significant disagreements found, ending debate")
            return debate_round
        
        logger.info(f"Found {len(disagreements)} disagreement points")
        
        # Generate debate prompt
        debate_prompt = self.generate_debate_prompt(previous_responses, disagreements, round_number)
        
        # Each agent responds to the debate
        for i, agent in enumerate(self.agents):
            try:
                logger.info(f"Agent {agent.name} participating in debate...")
                
                # Get agent's system prompt
                system_prompt = agent.get_system_prompt()
                
                # Combine with debate context
                full_prompt = debate_prompt
                
                # Get updated position
                response_text = agent.call_llm(system_prompt, full_prompt)
                parsed = agent.parse_llm_response(response_text)
                
                # Update response
                previous_recommendation = previous_responses[i].recommendation
                previous_confidence = previous_responses[i].confidence
                
                updated_response = previous_responses[i]
                updated_response.recommendation = parsed.get('recommendation', updated_response.recommendation)
                updated_response.confidence = float(parsed.get('confidence', updated_response.confidence))
                
                debate_round.add_response(updated_response)
                
                # Log debate contribution with position changes
                debate_round.add_debate({
                    'agent': agent.name,
                    'previous_position': {
                        'recommendation': previous_recommendation,
                        'confidence': previous_confidence
                    },
                    'new_position': {
                        'recommendation': updated_response.recommendation,
                        'confidence': updated_response.confidence
                    },
                    'changed': previous_recommendation != updated_response.recommendation,
                    'rebuttals': parsed.get('rebuttals', []),
                    'supporting_evidence': parsed.get('supporting_evidence', []),
                    'concessions': parsed.get('concessions', [])
                })
                
                logger.info(f"Agent {agent.name} updated: {updated_response.recommendation} (confidence: {updated_response.confidence:.2f})")
            
            except Exception as e:
                logger.error(f"Agent {agent.name} failed in debate: {e}")
                debate_round.add_response(previous_responses[i])
        
        logger.info(f"=== Debate Round {round_number} Complete ===")
        return debate_round
    
    def run_full_debate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run complete debate process
        
        Args:
            data: Formatted data for analysis
        
        Returns:
            Complete debate results
        """
        logger.info("========== STARTING MULTI-AGENT DEBATE ==========")
        
        # Initial analysis
        initial_responses = self.conduct_initial_analysis(data)
        
        if not initial_responses:
            logger.error("No agents provided initial analysis")
            return {
                'error': 'No agent responses received',
                'ticker': data.get('ticker'),
                'timestamp': datetime.now().isoformat()
            }
        
        # Store all rounds
        all_rounds = []
        current_responses = initial_responses
        
        # Initial round
        initial_round = DebateRound(0)
        for response in initial_responses:
            initial_round.add_response(response)
        all_rounds.append(initial_round)
        
        # Debate rounds
        for round_num in range(1, self.max_rounds + 1):
            debate_round = self.conduct_debate_round(data, current_responses, round_num)
            
            # Calculate consensus for this round
            if debate_round.agent_responses:
                current_responses = debate_round.agent_responses
                consensus = self.calculate_consensus(current_responses)
                debate_round.consensus_level = consensus
                logger.info(f"Round {round_num} consensus: {consensus:.1%}")
            
            all_rounds.append(debate_round)
            
            # Check for early consensus
            disagreements = self.identify_disagreements(current_responses)
            if not disagreements:
                logger.info(f"Consensus reached in round {round_num}")
                break
        
        # Compile results
        result = {
            'ticker': data.get('ticker'),
            'company_name': data.get('company_name'),
            'timestamp': datetime.now().isoformat(),
            'total_rounds': len(all_rounds),
            'rounds': [r.to_dict() for r in all_rounds],
            'final_responses': [
                {
                    'agent': r.agent_name,
                    'role': r.agent_role,
                    'recommendation': r.recommendation,
                    'confidence': r.confidence,
                    'reasoning': r.reasoning,
                    'key_points': r.key_points,
                    'risks': r.risks
                }
                for r in current_responses
            ]
        }
        
        # Log debate
        if self.enable_logging:
            self.reasoning_logger.log_debate(result)
        
        logger.info("========== DEBATE COMPLETE ==========")
        return result
