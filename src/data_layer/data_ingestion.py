"""
Data Ingestion Manager
Coordinates all data collection activities
"""

from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .stock_data import StockDataCollector
from .news_data import NewsDataCollector
from .financial_data import FinancialDataCollector
from ..config import config
from ..utils import ensure_dir, save_json


class DataIngestionManager:
    """Manages data collection from all sources"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = ensure_dir(cache_dir or config.settings.data_cache_dir)
        
        # Initialize collectors
        self.stock_collector = StockDataCollector(cache_dir=self.cache_dir)
        self.news_collector = NewsDataCollector(cache_dir=self.cache_dir)
        self.financial_collector = FinancialDataCollector(cache_dir=self.cache_dir)
    
    def ingest_all_data(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        period: str = "1mo",
        news_days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Ingest all data for a given ticker
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name for news search
            period: Period for stock price data
            news_days_back: Days to look back for news
        
        Returns:
            Dictionary with all collected data
        """
        logger.info(f"Starting complete data ingestion for {ticker}")
        
        # Collect stock data
        logger.info("Collecting stock data...")
        stock_data = self.stock_collector.collect_complete_stock_data(ticker, period=period)
        
        # Extract company name if not provided
        if not company_name and stock_data.get('company_info'):
            company_name = stock_data['company_info'].get('name', ticker)
        
        # Collect news data
        logger.info("Collecting news data...")
        news_data = self.news_collector.collect_all_news(
            ticker=ticker,
            company_name=company_name,
            days_back=news_days_back
        )
        
        # Collect financial data
        logger.info("Collecting financial data...")
        financial_data = self.financial_collector.collect_complete_financials(ticker)
        
        # Compile all data
        result = {
            'ticker': ticker,
            'company_name': company_name,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'stock': stock_data,
                'news': news_data,
                'financials': financial_data
            },
            'metadata': {
                'period': period,
                'news_days_back': news_days_back,
                'total_news_articles': news_data.get('total_articles', 0)
            }
        }
        
        # Save complete dataset
        output_file = self.cache_dir / f"{ticker}_complete_data.json"
        save_json(result, output_file)
        
        logger.info(f"Complete data ingestion finished for {ticker}")
        logger.info(f"Total news articles: {result['metadata']['total_news_articles']}")
        
        return result
    
    def refresh_stock_data(self, ticker: str, period: str = "1d") -> Dict[str, Any]:
        """Quick refresh of stock price data only"""
        logger.info(f"Refreshing stock data for {ticker}")
        return self.stock_collector.collect_complete_stock_data(ticker, period=period)
    
    def refresh_news_data(self, ticker: str, company_name: Optional[str] = None, days_back: int = 1) -> Dict[str, Any]:
        """Quick refresh of news data only"""
        logger.info(f"Refreshing news data for {ticker}")
        return self.news_collector.collect_all_news(ticker, company_name, days_back=days_back)
