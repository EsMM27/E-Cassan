"""
E-Cassan Main System
Orchestrates the complete AI trading agent workflow
"""

from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger
import sys

from .config import config
from .data_layer import DataIngestionManager, DataPipeline
from .agent_layer import AgentFactory
from .reasoning_layer import DebateManager, ConsensusBuilder, ReasoningLogger
from .decision_layer import SignalGenerator, DecisionLogger
from .utils import Timer, save_json


class ECassanSystem:
    """Main orchestrator for the E-Cassan trading agent system"""
    
    def __init__(
        self,
        use_finbert: bool = True,
        log_level: str = "INFO"
    ):
        """
        Initialize the E-Cassan system
        
        Args:
            use_finbert: Whether to use FinBERT for sentiment analysis
            log_level: Logging level
        """
        # Configure logging
        logger.remove()
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        )
        logger.add(
            Path(config.settings.log_dir) / "system.log",
            rotation="500 MB",
            retention="10 days",
            level=log_level
        )
        
        logger.info("=" * 80)
        logger.info("Initializing E-Cassan AI Trading Agent System")
        logger.info("=" * 80)
        
        # Initialize components
        self.data_manager = DataIngestionManager()
        self.data_pipeline = DataPipeline()
        self.agents = AgentFactory.create_all_agents(use_finbert=use_finbert)
        self.reasoning_logger = ReasoningLogger()
        self.debate_manager = DebateManager(self.agents, self.reasoning_logger)
        self.consensus_builder = ConsensusBuilder()
        self.signal_generator = SignalGenerator()
        self.decision_logger = DecisionLogger()
        
        # Set agent weights
        agent_weights = AgentFactory.get_agent_weights(self.agents)
        self.consensus_builder.set_agent_weights(agent_weights)
        
        logger.info(f"System initialized with {len(self.agents)} agents")
        logger.info("=" * 80)
    
    def analyze_stock(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        period: str = "1mo",
        news_days_back: int = 7,
        consensus_method: str = "weighted",
        save_outputs: bool = True
    ) -> Dict[str, Any]:
        """
        Perform complete analysis on a stock
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name (optional, will be fetched if not provided)
            period: Period for stock data
            news_days_back: Days to look back for news
            consensus_method: Method for building consensus
            save_outputs: Whether to save outputs to files
        
        Returns:
            Complete analysis results including trading signal
        """
        logger.info(f"\n{'=' * 80}")
        logger.info(f"STARTING ANALYSIS: {ticker}")
        logger.info(f"{'=' * 80}\n")
        
        with Timer(f"Complete analysis for {ticker}"):
            try:
                # Step 1: Data Ingestion
                logger.info("STEP 1: Data Ingestion")
                with Timer("Data ingestion"):
                    raw_data = self.data_manager.ingest_all_data(
                        ticker=ticker,
                        company_name=company_name,
                        period=period,
                        news_days_back=news_days_back
                    )
                
                # Step 2: Data Processing
                logger.info("\nSTEP 2: Data Processing")
                with Timer("Data processing"):
                    processed_data = self.data_pipeline.prepare_agent_input(raw_data)
                
                # Step 3: Agent Analysis & Debate
                logger.info("\nSTEP 3: Multi-Agent Analysis & Debate")
                with Timer("Debate process"):
                    debate_result = self.debate_manager.run_full_debate(processed_data)
                
                # Step 4: Consensus Building
                logger.info("\nSTEP 4: Consensus Building")
                with Timer("Consensus building"):
                    consensus_report = self.consensus_builder.generate_final_report(
                        debate_result,
                        consensus_method=consensus_method
                    )
                
                # Step 5: Signal Generation
                logger.info("\nSTEP 5: Trading Signal Generation")
                with Timer("Signal generation"):
                    current_price = raw_data.get('data', {}).get('stock', {}).get('company_info', {}).get('current_price')
                    trading_signal = self.signal_generator.generate_signal(
                        consensus_report,
                        current_price=current_price
                    )
                
                # Step 6: Logging & Output
                if save_outputs:
                    logger.info("\nSTEP 6: Saving Outputs")
                    
                    # Log signal
                    signal_path = self.decision_logger.log_signal(trading_signal)
                    
                    # Save formatted report
                    formatted_text = self.signal_generator.format_signal_for_output(trading_signal)
                    report_path = self.decision_logger.log_formatted_signal(trading_signal, formatted_text)
                    
                    # Append to history
                    self.decision_logger.append_to_history(trading_signal)
                    
                    # Save readable debate report
                    debate_report_path = self.reasoning_logger.save_readable_report(debate_result)
                    
                    logger.info(f"Signal saved: {signal_path}")
                    logger.info(f"Report saved: {report_path}")
                    logger.info(f"Debate log saved: {debate_report_path}")
                
                # Compile complete results
                result = {
                    'ticker': ticker,
                    'company_name': trading_signal.company_name,
                    'trading_signal': trading_signal.model_dump(),
                    'consensus_report': consensus_report,
                    'debate_result': debate_result,
                    'raw_data': raw_data
                }
                
                logger.info(f"\n{'=' * 80}")
                logger.info(f"ANALYSIS COMPLETE: {ticker}")
                logger.info(f"SIGNAL: {trading_signal.signal} (Confidence: {trading_signal.confidence:.1%})")
                logger.info(f"{'=' * 80}\n")
                
                return result
            
            except Exception as e:
                logger.error(f"Error during analysis: {e}")
                logger.exception(e)
                raise
    
    def quick_analysis(self, ticker: str) -> str:
        """
        Perform quick analysis and return formatted signal
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Formatted trading signal text
        """
        result = self.analyze_stock(ticker)
        signal = result['trading_signal']
        
        # Convert back to TradingSignal object for formatting
        from .decision_layer import TradingSignal
        signal_obj = TradingSignal(**signal)
        
        return self.signal_generator.format_signal_for_output(signal_obj)
    
    def batch_analysis(
        self,
        tickers: list[str],
        save_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze multiple stocks
        
        Args:
            tickers: List of stock tickers
            save_summary: Whether to save summary report
        
        Returns:
            Dictionary with results for all tickers
        """
        logger.info(f"\n{'=' * 80}")
        logger.info(f"BATCH ANALYSIS: {len(tickers)} stocks")
        logger.info(f"{'=' * 80}\n")
        
        results = {}
        successful = 0
        failed = 0
        
        for i, ticker in enumerate(tickers, 1):
            logger.info(f"\nAnalyzing {i}/{len(tickers)}: {ticker}")
            
            try:
                result = self.analyze_stock(ticker)
                results[ticker] = {
                    'status': 'success',
                    'signal': result['trading_signal']['signal'],
                    'confidence': result['trading_signal']['confidence']
                }
                successful += 1
            
            except Exception as e:
                logger.error(f"Failed to analyze {ticker}: {e}")
                results[ticker] = {
                    'status': 'failed',
                    'error': str(e)
                }
                failed += 1
        
        summary = {
            'total': len(tickers),
            'successful': successful,
            'failed': failed,
            'results': results
        }
        
        if save_summary:
            from .utils import get_timestamp
            summary_file = Path(config.settings.output_dir) / f"batch_summary_{get_timestamp()}.json"
            save_json(summary, summary_file)
            logger.info(f"\nBatch summary saved: {summary_file}")
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"BATCH ANALYSIS COMPLETE")
        logger.info(f"Successful: {successful}/{len(tickers)}")
        logger.info(f"{'=' * 80}\n")
        
        return summary
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and configuration
        
        Returns:
            System status dictionary
        """
        return {
            'system': 'E-Cassan AI Trading Agent System',
            'version': '0.1.0',
            'agents': [
                {
                    'name': agent.name,
                    'role': agent.role,
                    'weight': agent.weight
                }
                for agent in self.agents
            ],
            'config': {
                'max_debate_rounds': config.reasoning_config.get('max_debate_rounds'),
                'consensus_threshold': config.reasoning_config.get('consensus_threshold'),
                'llm_model': config.model_config.get('llm', {}).get('model_name'),
                'sentiment_model': config.model_config.get('sentiment', {}).get('model_name')
            }
        }


def main():
    """Main entry point for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='E-Cassan AI Trading Agent System')
    parser.add_argument('ticker', help='Stock ticker symbol to analyze')
    parser.add_argument('--company-name', help='Company name (optional)')
    parser.add_argument('--period', default='1mo', help='Period for stock data (default: 1mo)')
    parser.add_argument('--news-days', type=int, default=7, help='Days to look back for news (default: 7)')
    parser.add_argument('--no-finbert', action='store_true', help='Disable FinBERT sentiment analysis')
    parser.add_argument('--log-level', default='INFO', help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Initialize system
    system = ECassanSystem(
        use_finbert=not args.no_finbert,
        log_level=args.log_level
    )
    
    # Run analysis
    result = system.quick_analysis(args.ticker)
    
    # Print result
    print(result)


if __name__ == '__main__':
    main()
