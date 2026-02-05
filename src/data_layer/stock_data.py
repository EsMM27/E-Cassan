"""
Stock Data Collector
Collects stock price data, technical indicators, and historical information
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time
import yfinance as yf
import pandas as pd
import ta
from loguru import logger

from ..config import config
from ..utils import ensure_dir, save_json, calculate_date_range


class StockDataCollector:
    """Collects and processes stock market data"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = ensure_dir(cache_dir or config.settings.data_cache_dir)
    
    def get_stock_data(
        self,
        ticker: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch stock data from Yahoo Finance
        
        Args:
            ticker: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            logger.info(f"Fetching stock data for {ticker}")
            time.sleep(1)  # Rate limiting: wait 1 second between API calls
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data retrieved for {ticker}")
                return pd.DataFrame()
            
            logger.info(f"Retrieved {len(df)} data points for {ticker}")
            return df
        
        except Exception as e:
            logger.error(f"Error fetching stock data for {ticker}: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            DataFrame with technical indicators added
        """
        if df.empty:
            return df
        
        try:
            # Moving Averages
            df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12)
            df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26)
            
            # MACD
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Diff'] = macd.macd_diff()
            
            # RSI
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(df['Close'])
            df['BB_High'] = bollinger.bollinger_hband()
            df['BB_Low'] = bollinger.bollinger_lband()
            df['BB_Mid'] = bollinger.bollinger_mavg()
            
            # Volume indicators
            df['Volume_SMA'] = ta.volume.volume_weighted_average_price(
                df['High'], df['Low'], df['Close'], df['Volume']
            )
            
            # ATR (Average True Range)
            df['ATR'] = ta.volatility.average_true_range(
                df['High'], df['Low'], df['Close'], window=14
            )
            
            logger.info("Technical indicators calculated successfully")
            return df
        
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get company information
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with company information
        """
        try:
            time.sleep(1)  # Rate limiting: wait 1 second between API calls
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract key information
            company_data = {
                'ticker': ticker,
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'employees': info.get('fullTimeEmployees', 0),
                'description': info.get('longBusinessSummary', ''),
                'website': info.get('website', ''),
                'current_price': info.get('currentPrice', 0),
                'previous_close': info.get('previousClose', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'profit_margins': info.get('profitMargins', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
            }
            
            logger.info(f"Retrieved company info for {ticker}")
            return company_data
        
        except Exception as e:
            logger.error(f"Error fetching company info for {ticker}: {e}")
            return {'ticker': ticker, 'error': str(e)}
    
    def get_financial_statements(self, ticker: str) -> Dict[str, Any]:
        """
        Get financial statements (income statement, balance sheet, cash flow)
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with financial statements
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Helper to convert DataFrame with Timestamp columns to JSON-serializable dict
            def df_to_dict(df):
                if df is None or df.empty:
                    return {}
                # Convert Timestamp column names to strings
                df_copy = df.copy()
                df_copy.columns = [str(col) for col in df_copy.columns]
                return df_copy.to_dict()
            
            financials = {
                'income_statement': df_to_dict(stock.financials) if hasattr(stock, 'financials') else {},
                'balance_sheet': df_to_dict(stock.balance_sheet) if hasattr(stock, 'balance_sheet') else {},
                'cash_flow': df_to_dict(stock.cashflow) if hasattr(stock, 'cashflow') else {},
                'quarterly_financials': df_to_dict(stock.quarterly_financials) if hasattr(stock, 'quarterly_financials') else {}
            }
            
            logger.info(f"Retrieved financial statements for {ticker}")
            return financials
        
        except Exception as e:
            logger.error(f"Error fetching financial statements for {ticker}: {e}")
            return {}
    
    def collect_complete_stock_data(self, ticker: str, period: str = "1mo") -> Dict[str, Any]:
        """
        Collect all stock-related data
        
        Args:
            ticker: Stock ticker symbol
            period: Time period for price data
        
        Returns:
            Dictionary with all stock data
        """
        logger.info(f"Collecting complete stock data for {ticker}")
        
        # Get price data with technical indicators
        price_data = self.get_stock_data(ticker, period=period)
        price_data_with_indicators = self.calculate_technical_indicators(price_data)
        
        # Get company info
        company_info = self.get_company_info(ticker)
        
        # Get financial statements
        financials = self.get_financial_statements(ticker)
        
        # Helper to convert DataFrame to JSON-serializable dict
        def safe_to_dict(df):
            if df.empty:
                return {}
            df_copy = df.copy()
            # Convert index to string if it's a DatetimeIndex
            if hasattr(df_copy.index, 'strftime'):
                df_copy.index = df_copy.index.strftime('%Y-%m-%d %H:%M:%S')
            return df_copy.to_dict()
        
        # Compile results
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'company_info': company_info,
            'price_data': {
                'latest': price_data_with_indicators.iloc[-1].to_dict() if not price_data_with_indicators.empty else {},
                'historical': safe_to_dict(price_data_with_indicators.tail(30))
            },
            'financials': financials
        }
        
        # Save to cache
        cache_file = self.cache_dir / f"{ticker}_stock_data.json"
        save_json(result, cache_file)
        
        logger.info(f"Complete stock data collection finished for {ticker}")
        return result
