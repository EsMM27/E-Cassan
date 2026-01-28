"""
Financial Data Collector
Collects earnings reports, SEC filings, and other financial documents
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from loguru import logger

from ..config import config
from ..utils import ensure_dir, save_json


class FinancialDataCollector:
    """Collects financial data and regulatory filings"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = ensure_dir(cache_dir or config.settings.data_cache_dir)
        self.alpha_vantage_key = config.settings.alpha_vantage_api_key
    
    def get_earnings_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch earnings data from Alpha Vantage
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with earnings data
        """
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return {}
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'EARNINGS',
                'symbol': ticker,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return {}
            
            result = {
                'ticker': ticker,
                'quarterly_earnings': data.get('quarterlyEarnings', []),
                'annual_earnings': data.get('annualEarnings', [])
            }
            
            logger.info(f"Retrieved earnings data for {ticker}")
            return result
        
        except Exception as e:
            logger.error(f"Error fetching earnings data: {e}")
            return {}
    
    def get_income_statement(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch income statement from Alpha Vantage
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with income statement data
        """
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return {}
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'INCOME_STATEMENT',
                'symbol': ticker,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return {}
            
            result = {
                'ticker': ticker,
                'quarterly_reports': data.get('quarterlyReports', []),
                'annual_reports': data.get('annualReports', [])
            }
            
            logger.info(f"Retrieved income statement for {ticker}")
            return result
        
        except Exception as e:
            logger.error(f"Error fetching income statement: {e}")
            return {}
    
    def get_balance_sheet(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch balance sheet from Alpha Vantage
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with balance sheet data
        """
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return {}
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'BALANCE_SHEET',
                'symbol': ticker,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return {}
            
            result = {
                'ticker': ticker,
                'quarterly_reports': data.get('quarterlyReports', []),
                'annual_reports': data.get('annualReports', [])
            }
            
            logger.info(f"Retrieved balance sheet for {ticker}")
            return result
        
        except Exception as e:
            logger.error(f"Error fetching balance sheet: {e}")
            return {}
    
    def get_cash_flow(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch cash flow statement from Alpha Vantage
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with cash flow data
        """
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return {}
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'CASH_FLOW',
                'symbol': ticker,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return {}
            
            result = {
                'ticker': ticker,
                'quarterly_reports': data.get('quarterlyReports', []),
                'annual_reports': data.get('annualReports', [])
            }
            
            logger.info(f"Retrieved cash flow statement for {ticker}")
            return result
        
        except Exception as e:
            logger.error(f"Error fetching cash flow: {e}")
            return {}
    
    def get_company_overview(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch company overview from Alpha Vantage
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with company overview
        """
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return {}
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'OVERVIEW',
                'symbol': ticker,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return {}
            
            logger.info(f"Retrieved company overview for {ticker}")
            return data
        
        except Exception as e:
            logger.error(f"Error fetching company overview: {e}")
            return {}
    
    def collect_complete_financials(self, ticker: str) -> Dict[str, Any]:
        """
        Collect all financial data for a ticker
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with all financial data
        """
        logger.info(f"Collecting complete financial data for {ticker}")
        
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'company_overview': self.get_company_overview(ticker),
            'earnings': self.get_earnings_data(ticker),
            'income_statement': self.get_income_statement(ticker),
            'balance_sheet': self.get_balance_sheet(ticker),
            'cash_flow': self.get_cash_flow(ticker)
        }
        
        # Save to cache
        cache_file = self.cache_dir / f"{ticker}_financials.json"
        save_json(result, cache_file)
        
        logger.info(f"Complete financial data collection finished for {ticker}")
        return result
