"""
Decision Logger
Maintains comprehensive logs of all trading signals and decisions
"""

from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger
import json

from .signal_generator import TradingSignal
from ..config import config
from ..utils import ensure_dir, save_json, get_timestamp


class DecisionLogger:
    """Logs all trading signals for audit trail"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize decision logger
        
        Args:
            output_dir: Directory to store decision logs
        """
        self.output_dir = ensure_dir(output_dir or config.settings.output_dir)
        self.signals_dir = ensure_dir(self.output_dir / "signals")
        self.reports_dir = ensure_dir(self.output_dir / "reports")
        
        logger.info(f"DecisionLogger initialized: {self.output_dir}")
    
    def log_signal(self, signal: TradingSignal) -> Path:
        """
        Log trading signal to file
        
        Args:
            signal: TradingSignal object
        
        Returns:
            Path to log file
        """
        ticker = signal.ticker
        timestamp = get_timestamp()
        
        # Save as JSON
        filename = f"{ticker}_signal_{timestamp}.json"
        filepath = self.signals_dir / filename
        
        # Convert to dict and save
        signal_dict = signal.model_dump()
        save_json(signal_dict, filepath, indent=2)
        
        logger.info(f"Signal logged: {filepath}")
        return filepath
    
    def log_formatted_signal(self, signal: TradingSignal, formatted_text: str) -> Path:
        """
        Log formatted signal report
        
        Args:
            signal: TradingSignal object
            formatted_text: Formatted text output
        
        Returns:
            Path to report file
        """
        ticker = signal.ticker
        timestamp = get_timestamp()
        
        filename = f"{ticker}_report_{timestamp}.txt"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        logger.info(f"Formatted signal saved: {filepath}")
        return filepath
    
    def create_signal_summary(self, signal: TradingSignal) -> Dict[str, Any]:
        """
        Create concise summary of signal for quick reference
        
        Args:
            signal: TradingSignal object
        
        Returns:
            Summary dictionary
        """
        return {
            'ticker': signal.ticker,
            'company_name': signal.company_name,
            'timestamp': signal.timestamp,
            'signal': signal.signal,
            'confidence': signal.confidence,
            'consensus_level': signal.consensus_level,
            'price_target': signal.price_target,
            'stop_loss': signal.stop_loss,
            'time_horizon': signal.time_horizon,
            'top_factors': signal.key_factors[:3],
            'top_risks': signal.risks[:3]
        }
    
    def append_to_history(self, signal: TradingSignal):
        """
        Append signal to historical log file
        
        Args:
            signal: TradingSignal object
        """
        history_file = self.output_dir / "signal_history.jsonl"
        
        summary = self.create_signal_summary(signal)
        
        # Append to JSONL file (one JSON per line)
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(summary, ensure_ascii=False) + '\n')
        
        logger.info(f"Signal appended to history: {history_file}")
    
    def get_signal_history(
        self,
        ticker: Optional[str] = None,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Retrieve signal history
        
        Args:
            ticker: Optional ticker to filter by
            limit: Maximum number of signals to return
        
        Returns:
            List of signal summaries
        """
        history_file = self.output_dir / "signal_history.jsonl"
        
        if not history_file.exists():
            return []
        
        signals = []
        with open(history_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    signal = json.loads(line.strip())
                    if ticker is None or signal.get('ticker') == ticker:
                        signals.append(signal)
                except json.JSONDecodeError:
                    continue
        
        # Return most recent first
        signals.reverse()
        return signals[:limit]
    
    def generate_performance_report(
        self,
        ticker: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate performance statistics from historical signals
        
        Args:
            ticker: Optional ticker to filter by
        
        Returns:
            Performance statistics
        """
        history = self.get_signal_history(ticker=ticker, limit=1000)
        
        if not history:
            return {
                'total_signals': 0,
                'message': 'No historical signals found'
            }
        
        # Calculate statistics
        total = len(history)
        buy_signals = sum(1 for s in history if 'BUY' in s['signal'])
        sell_signals = sum(1 for s in history if 'SELL' in s['signal'])
        hold_signals = sum(1 for s in history if s['signal'] == 'HOLD')
        
        avg_confidence = sum(s['confidence'] for s in history) / total
        avg_consensus = sum(s['consensus_level'] for s in history) / total
        
        # Time horizon breakdown
        time_horizons = {}
        for signal in history:
            horizon = signal.get('time_horizon', 'unknown')
            time_horizons[horizon] = time_horizons.get(horizon, 0) + 1
        
        return {
            'total_signals': total,
            'signal_breakdown': {
                'buy': buy_signals,
                'sell': sell_signals,
                'hold': hold_signals
            },
            'average_confidence': avg_confidence,
            'average_consensus': avg_consensus,
            'time_horizon_breakdown': time_horizons,
            'tickers_analyzed': len(set(s['ticker'] for s in history))
        }
    
    def export_signals_csv(
        self,
        output_path: Optional[Path] = None,
        ticker: Optional[str] = None
    ) -> Path:
        """
        Export signals to CSV format
        
        Args:
            output_path: Path to save CSV (optional)
            ticker: Optional ticker to filter by
        
        Returns:
            Path to CSV file
        """
        import csv
        
        if output_path is None:
            timestamp = get_timestamp()
            filename = f"signals_export_{timestamp}.csv"
            output_path = self.output_dir / filename
        
        history = self.get_signal_history(ticker=ticker, limit=10000)
        
        if not history:
            logger.warning("No signals to export")
            return output_path
        
        # Define CSV columns
        fieldnames = [
            'ticker', 'company_name', 'timestamp', 'signal',
            'confidence', 'consensus_level', 'price_target',
            'stop_loss', 'time_horizon'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for signal in history:
                row = {key: signal.get(key, '') for key in fieldnames}
                writer.writerow(row)
        
        logger.info(f"Signals exported to CSV: {output_path}")
        return output_path
    
    def get_latest_signal(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get most recent signal for a ticker
        
        Args:
            ticker: Stock ticker
        
        Returns:
            Latest signal summary or None
        """
        history = self.get_signal_history(ticker=ticker, limit=1)
        return history[0] if history else None
