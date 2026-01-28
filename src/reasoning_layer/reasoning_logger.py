"""
Reasoning Logger
Logs agent reasoning, debates, and decisions for auditability
"""

from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from loguru import logger
import json

from ..config import config
from ..utils import ensure_dir, save_json, get_timestamp


class ReasoningLogger:
    """Logs all reasoning processes for transparency and audit"""
    
    def __init__(self, log_dir: str = None):
        """
        Initialize reasoning logger
        
        Args:
            log_dir: Directory to store reasoning logs
        """
        self.log_dir = ensure_dir(log_dir or Path(config.settings.log_dir) / "reasoning")
        logger.info(f"ReasoningLogger initialized: {self.log_dir}")
    
    def log_debate(self, debate_result: Dict[str, Any]) -> Path:
        """
        Log complete debate results
        
        Args:
            debate_result: Debate results from DebateManager
        
        Returns:
            Path to log file
        """
        ticker = debate_result.get('ticker', 'UNKNOWN')
        timestamp = get_timestamp()
        
        filename = f"{ticker}_debate_{timestamp}.json"
        filepath = self.log_dir / filename
        
        save_json(debate_result, filepath, indent=2)
        logger.info(f"Debate logged: {filepath}")
        
        return filepath
    
    def log_consensus(self, consensus_result: Dict[str, Any]) -> Path:
        """
        Log consensus building results
        
        Args:
            consensus_result: Consensus results
        
        Returns:
            Path to log file
        """
        ticker = consensus_result.get('ticker', 'UNKNOWN')
        timestamp = get_timestamp()
        
        filename = f"{ticker}_consensus_{timestamp}.json"
        filepath = self.log_dir / filename
        
        save_json(consensus_result, filepath, indent=2)
        logger.info(f"Consensus logged: {filepath}")
        
        return filepath
    
    def log_agent_response(
        self,
        agent_name: str,
        response: Dict[str, Any],
        ticker: str
    ) -> Path:
        """
        Log individual agent response
        
        Args:
            agent_name: Name of the agent
            response: Agent response data
            ticker: Stock ticker
        
        Returns:
            Path to log file
        """
        timestamp = get_timestamp()
        
        filename = f"{ticker}_{agent_name}_{timestamp}.json"
        filepath = self.log_dir / "agents" / filename
        ensure_dir(filepath.parent)
        
        save_json(response, filepath, indent=2)
        
        return filepath
    
    def generate_readable_report(self, debate_result: Dict[str, Any]) -> str:
        """
        Generate human-readable report from debate results
        
        Args:
            debate_result: Debate results
        
        Returns:
            Formatted report string
        """
        ticker = debate_result.get('ticker', 'Unknown')
        company_name = debate_result.get('company_name', 'Unknown')
        timestamp = debate_result.get('timestamp', 'Unknown')
        total_rounds = debate_result.get('total_rounds', 0)
        
        report = f"""
{'=' * 80}
AI TRADING AGENT SYSTEM - ANALYSIS REPORT
{'=' * 80}

Company: {company_name} ({ticker})
Analysis Date: {timestamp}
Total Debate Rounds: {total_rounds}

{'=' * 80}
AGENT ANALYSES
{'=' * 80}

"""
        
        # Add each agent's final position
        for response in debate_result.get('final_responses', []):
            report += f"""
{'_' * 80}
{response['role']} ({response['agent']})
{'_' * 80}

Recommendation: {response['recommendation']}
Confidence: {response['confidence']:.2%}

Reasoning:
{response['reasoning']}

Key Points:
"""
            for point in response['key_points']:
                report += f"  • {point}\n"
            
            report += "\nRisks:\n"
            for risk in response['risks']:
                report += f"  ⚠ {risk}\n"
            
            report += "\n"
        
        # Add debate summary
        report += f"""
{'=' * 80}
DEBATE SUMMARY
{'=' * 80}

"""
        
        rounds = debate_result.get('rounds', [])
        for round_data in rounds[1:]:  # Skip initial round
            round_num = round_data.get('round_number', 0)
            report += f"\nRound {round_num}:\n"
            
            for debate in round_data.get('debates', []):
                agent = debate.get('agent', 'Unknown')
                report += f"\n{agent}:\n"
                
                if debate.get('rebuttals'):
                    report += "  Rebuttals:\n"
                    for rebuttal in debate['rebuttals']:
                        report += f"    - {rebuttal}\n"
                
                if debate.get('concessions'):
                    report += "  Concessions:\n"
                    for concession in debate['concessions']:
                        report += f"    - {concession}\n"
        
        report += f"\n{'=' * 80}\n"
        
        return report
    
    def save_readable_report(
        self,
        debate_result: Dict[str, Any]
    ) -> Path:
        """
        Save human-readable report to file
        
        Args:
            debate_result: Debate results
        
        Returns:
            Path to report file
        """
        ticker = debate_result.get('ticker', 'UNKNOWN')
        timestamp = get_timestamp()
        
        report = self.generate_readable_report(debate_result)
        
        filename = f"{ticker}_report_{timestamp}.txt"
        filepath = self.log_dir / "reports" / filename
        ensure_dir(filepath.parent)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Readable report saved: {filepath}")
        return filepath
    
    def get_recent_logs(self, ticker: str = None, limit: int = 10) -> list[Path]:
        """
        Get most recent log files
        
        Args:
            ticker: Optional ticker to filter by
            limit: Maximum number of logs to return
        
        Returns:
            List of log file paths
        """
        pattern = f"{ticker}_*" if ticker else "*"
        logs = sorted(
            self.log_dir.glob(f"{pattern}.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return logs[:limit]
