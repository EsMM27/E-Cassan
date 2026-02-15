"""
Signal Generator
Converts consensus recommendations into actionable trading signals
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger

from ..config import config


class TradingSignal(BaseModel):
    """Trading signal with full context"""
    ticker: str
    company_name: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Core signal
    signal: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL, SHORT, STRONG_SHORT
    confidence: float = Field(ge=0.0, le=1.0)
    consensus_level: float = Field(ge=0.0, le=1.0)
    
    # Recommendation breakdown
    agent_breakdown: Dict[str, int]  # Count of each recommendation
    weighted_scores: Dict[str, float]  # Weighted scores for each signal
    
    # Supporting information
    key_factors: list[str]  # Top factors supporting the signal
    risks: list[str]  # Key risks to consider
    agent_consensus: str  # Summary of agent agreement
    
    # Quantitative metrics
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    time_horizon: Optional[str] = None  # short_term, medium_term, long_term
    
    # Metadata
    total_agents: int
    debate_rounds: int
    methodology: str  # weighted, majority, confidence
    
    # Full context
    reasoning_summary: str
    individual_agent_views: list[Dict[str, Any]]


class SignalGenerator:
    """Generates trading signals from consensus"""
    
    def __init__(self):
        """Initialize signal generator"""
        self.signal_types = config.decision_config.get('signal_types', [
            'STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL', 'SHORT', 'STRONG_SHORT'
        ])
        
        self.confidence_thresholds = config.decision_config.get('confidence_levels', {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        })
        
        logger.info("SignalGenerator initialized")
    
    def determine_signal_strength(
        self,
        recommendation: str,
        confidence: float,
        consensus_level: float
    ) -> str:
        """
        Determine signal strength based on confidence and consensus
        
        Args:
            recommendation: Base recommendation (BUY/SELL/SHORT/HOLD)
            confidence: Confidence level (0-1)
            consensus_level: Level of consensus among agents (0-1)
        
        Returns:
            Signal strength (e.g., STRONG_BUY, BUY, SHORT, STRONG_SHORT, HOLD)
        """
        # High confidence and high consensus = STRONG signal
        high_threshold = self.confidence_thresholds['high']
        medium_threshold = self.confidence_thresholds['medium']
        
        if recommendation == 'BUY':
            if confidence >= high_threshold and consensus_level >= 0.75:
                return 'STRONG_BUY'
            else:
                return 'BUY'
        
        elif recommendation == 'SELL':
            if confidence >= high_threshold and consensus_level >= 0.75:
                return 'STRONG_SELL'
            else:
                return 'SELL'
        
        elif recommendation == 'SHORT':
            if confidence >= high_threshold and consensus_level >= 0.75:
                return 'STRONG_SHORT'
            else:
                return 'SHORT'
        
        else:  # HOLD
            return 'HOLD'
    
    def extract_key_factors(
        self,
        consensus_report: Dict[str, Any],
        top_n: int = 5
    ) -> list[str]:
        """
        Extract top factors supporting the signal
        
        Args:
            consensus_report: Consensus report
            top_n: Number of top factors to extract
        
        Returns:
            List of key factors
        """
        aggregated = consensus_report.get('aggregated_analysis', {})
        all_key_points = aggregated.get('key_points', [])
        
        # For now, return top N points
        # Could implement more sophisticated ranking later
        return all_key_points[:top_n]
    
    def extract_risks(
        self,
        consensus_report: Dict[str, Any],
        top_n: int = 5
    ) -> list[str]:
        """
        Extract top risks
        
        Args:
            consensus_report: Consensus report
            top_n: Number of top risks to extract
        
        Returns:
            List of key risks
        """
        aggregated = consensus_report.get('aggregated_analysis', {})
        all_risks = aggregated.get('risks', [])
        
        return all_risks[:top_n]
    
    def generate_consensus_summary(
        self,
        consensus_report: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable consensus summary
        
        Args:
            consensus_report: Consensus report
        
        Returns:
            Summary string
        """
        consensus = consensus_report.get('consensus', {})
        recommendation = consensus.get('recommendation', 'HOLD')
        confidence = consensus.get('confidence', 0.0)
        consensus_level = consensus.get('consensus_level', 0.0)
        breakdown = consensus.get('breakdown', {})
        
        summary = f"{recommendation} recommendation with {confidence:.1%} confidence. "
        summary += f"Consensus level: {consensus_level:.1%}. "
        summary += f"Agent breakdown: {breakdown.get('BUY', 0)} BUY, "
        summary += f"{breakdown.get('HOLD', 0)} HOLD, "
        summary += f"{breakdown.get('SELL', 0)} SELL, "
        summary += f"{breakdown.get('SHORT', 0)} SHORT."
        
        return summary
    
    def generate_reasoning_summary(
        self,
        consensus_report: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive reasoning summary
        
        Args:
            consensus_report: Consensus report
        
        Returns:
            Reasoning summary
        """
        aggregated = consensus_report.get('aggregated_analysis', {})
        agent_reasoning = aggregated.get('agent_reasoning', [])
        
        summary = "## Agent Reasoning:\n\n"
        for reasoning in agent_reasoning:
            summary += f"{reasoning}\n\n"
        
        return summary
    
    def estimate_price_targets(
        self,
        consensus_report: Dict[str, Any],
        current_price: Optional[float] = None
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Estimate price target and stop loss
        
        Args:
            consensus_report: Consensus report
            current_price: Current stock price
        
        Returns:
            Tuple of (price_target, stop_loss)
        """
        # This is a simplified placeholder
        # In a real system, you'd analyze technical levels, volatility, etc.
        
        if not current_price:
            return None, None
        
        consensus = consensus_report.get('consensus', {})
        recommendation = consensus.get('recommendation', 'HOLD')
        confidence = consensus.get('confidence', 0.5)
        
        if recommendation == 'BUY':
            # Target: 5-15% upside based on confidence
            target_pct = 0.05 + (confidence * 0.10)
            price_target = current_price * (1 + target_pct)
            
            # Stop loss: 3-5% below
            stop_loss = current_price * 0.95
            
        elif recommendation == 'SELL':
            # Target: 5-15% downside
            target_pct = 0.05 + (confidence * 0.10)
            price_target = current_price * (1 - target_pct)
            
            # Stop loss: 3-5% above
            stop_loss = current_price * 1.05
        
        elif recommendation == 'SHORT':
            # Target: 10-25% downside (more aggressive than SELL)
            target_pct = 0.10 + (confidence * 0.15)
            price_target = current_price * (1 - target_pct)
            
            # Stop loss: 5-8% above (tighter than SELL)
            stop_loss_pct = 0.05 + (0.03 * (1 - confidence))
            stop_loss = current_price * (1 + stop_loss_pct)
        
        else:  # HOLD
            price_target = current_price
            stop_loss = current_price * 0.90
        
        return price_target, stop_loss
    
    def determine_time_horizon(
        self,
        consensus_report: Dict[str, Any]
    ) -> str:
        """
        Determine investment time horizon
        
        Args:
            consensus_report: Consensus report
        
        Returns:
            Time horizon (short_term, medium_term, long_term)
        """
        # Placeholder logic
        # In real system, analyze agent inputs for time-specific signals
        
        consensus = consensus_report.get('consensus', {})
        confidence = consensus.get('confidence', 0.5)
        
        # Higher confidence = longer horizon
        if confidence >= 0.8:
            return 'long_term'
        elif confidence >= 0.6:
            return 'medium_term'
        else:
            return 'short_term'
    
    def generate_signal(
        self,
        consensus_report: Dict[str, Any],
        current_price: Optional[float] = None
    ) -> TradingSignal:
        """
        Generate complete trading signal from consensus report
        
        Args:
            consensus_report: Consensus report from ConsensusBuilder
            current_price: Current stock price (optional)
        
        Returns:
            TradingSignal object
        """
        logger.info(f"Generating trading signal for {consensus_report.get('ticker')}")
        
        # Extract core data
        consensus = consensus_report.get('consensus', {})
        recommendation = consensus.get('recommendation', 'HOLD')
        confidence = consensus.get('confidence', 0.0)
        consensus_level = consensus.get('consensus_level', 0.0)
        
        # Determine signal strength
        signal = self.determine_signal_strength(
            recommendation,
            confidence,
            consensus_level
        )
        
        # Extract supporting information
        key_factors = self.extract_key_factors(consensus_report)
        risks = self.extract_risks(consensus_report)
        agent_consensus_text = self.generate_consensus_summary(consensus_report)
        reasoning_summary = self.generate_reasoning_summary(consensus_report)
        
        # Estimate targets
        price_target, stop_loss = self.estimate_price_targets(
            consensus_report,
            current_price
        )
        
        # Determine time horizon
        time_horizon = self.determine_time_horizon(consensus_report)
        
        # Create trading signal
        trading_signal = TradingSignal(
            ticker=consensus_report.get('ticker', 'UNKNOWN'),
            company_name=consensus_report.get('company_name', 'Unknown'),
            signal=signal,
            confidence=confidence,
            consensus_level=consensus_level,
            agent_breakdown=consensus.get('breakdown', {}),
            weighted_scores=consensus.get('weighted_scores', {}),
            key_factors=key_factors,
            risks=risks,
            agent_consensus=agent_consensus_text,
            price_target=price_target,
            stop_loss=stop_loss,
            time_horizon=time_horizon,
            total_agents=consensus_report.get('debate_summary', {}).get('participating_agents', 0),
            debate_rounds=consensus_report.get('debate_summary', {}).get('total_rounds', 0),
            methodology=consensus.get('method', 'weighted'),
            reasoning_summary=reasoning_summary,
            individual_agent_views=consensus_report.get('individual_positions', [])
        )
        
        logger.info(f"Signal generated: {signal} with {confidence:.1%} confidence")
        return trading_signal
    
    def format_signal_for_output(self, signal: TradingSignal) -> str:
        """
        Format trading signal as human-readable text
        
        Args:
            signal: TradingSignal object
        
        Returns:
            Formatted string
        """
        output = f"""
{'=' * 80}
TRADING SIGNAL
{'=' * 80}

Company: {signal.company_name} ({signal.ticker})
Generated: {signal.timestamp}

{'=' * 80}
RECOMMENDATION: {signal.signal}
{'=' * 80}

Confidence: {signal.confidence:.1%}
Consensus Level: {signal.consensus_level:.1%}
Time Horizon: {signal.time_horizon.replace('_', ' ').title()}

"""
        
        if signal.price_target:
            output += f"Price Target: ${signal.price_target:.2f}\n"
        if signal.stop_loss:
            output += f"Stop Loss: ${signal.stop_loss:.2f}\n"
        
        output += f"""
{'=' * 80}
AGENT CONSENSUS
{'=' * 80}

{signal.agent_consensus}

Agent Votes:
- BUY: {signal.agent_breakdown.get('BUY', 0)}
- HOLD: {signal.agent_breakdown.get('HOLD', 0)}
- SELL: {signal.agent_breakdown.get('SELL', 0)}
- SHORT: {signal.agent_breakdown.get('SHORT', 0)}

{'=' * 80}
KEY SUPPORTING FACTORS
{'=' * 80}

"""
        for i, factor in enumerate(signal.key_factors, 1):
            output += f"{i}. {factor}\n"
        
        output += f"""
{'=' * 80}
KEY RISKS
{'=' * 80}

"""
        for i, risk in enumerate(signal.risks, 1):
            output += f"{i}. {risk}\n"
        
        output += f"""
{'=' * 80}
METHODOLOGY
{'=' * 80}

Total Agents: {signal.total_agents}
Debate Rounds: {signal.debate_rounds}
Consensus Method: {signal.methodology.title()}

{signal.reasoning_summary}

{'=' * 80}
"""
        
        return output
