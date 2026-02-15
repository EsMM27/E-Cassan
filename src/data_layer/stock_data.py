"""
Stock Data Collector
Collects stock price data, technical indicators, and historical information
Migrated from yfinance to Alpha Vantage + Finnhub for improved reliability
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time
import requests
import pandas as pd
import ta
from loguru import logger

from ..config import config
from ..utils import ensure_dir, save_json, calculate_date_range


class StockDataCollector:
    """Collects and processes stock market data"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = ensure_dir(cache_dir or config.settings.data_cache_dir)
        self.alpha_vantage_key = config.settings.alpha_vantage_api_key
        self.finnhub_key = config.settings.finnhub_api_key
    
    def get_stock_data(
        self,
        ticker: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch stock data from Alpha Vantage
        
        Args:
            ticker: Stock ticker symbol
            period: Time period (for compatibility, used with Finnhub fallback)
            interval: Data interval (only 1d is reliably supported for historical data)
        
        Returns:
            DataFrame with OHLCV data
        """
        # Try Alpha Vantage first
        data = self._get_stock_data_alpha_vantage(ticker)
        
        # Fallback to Finnhub if Alpha Vantage fails
        if data.empty and self.finnhub_key:
            logger.warning(f"Alpha Vantage failed for {ticker}, trying Finnhub...")
            data = self._get_stock_data_finnhub(ticker)
        
        if data.empty:
            logger.warning(f"No data retrieved for {ticker}")
        else:
            logger.info(f"Retrieved {len(data)} data points for {ticker}")
        
        return data
    
    def _get_stock_data_alpha_vantage(self, ticker: str) -> pd.DataFrame:
        """Fetch stock data from Alpha Vantage TIME_SERIES_DAILY endpoint"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return pd.DataFrame()
        
        try:
            time.sleep(0.2)  # Rate limiting
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': ticker,
                'apikey': self.alpha_vantage_key,
                'outputsize': 'full'
            }
            
            logger.debug(f"Requesting Alpha Vantage for {ticker}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for various error/limit responses from Alpha Vantage
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return pd.DataFrame()
            
            if 'Information' in data:
                logger.warning(f"Alpha Vantage rate limit hit: {data['Information']}")
                logger.warning("Suggestion: Free tier limited to 5 calls/min. Increase delay or use API key with more quota")
                return pd.DataFrame()
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage note: {data['Note']}")
                return pd.DataFrame()
            
            if 'Time Series (Daily)' not in data:
                logger.error(f"Unexpected response format from Alpha Vantage for {ticker}")
                logger.debug(f"Response keys: {list(data.keys())}")
                logger.debug(f"Full response (first 500 chars): {str(data)[:500]}")
                
                # Check if it's a valid response but just empty
                if 'Meta Data' in data:
                    logger.warning(f"Got metadata but no time series data for {ticker}")
                
                return pd.DataFrame()
            
            # Parse time series data
            time_series = data['Time Series (Daily)']
            
            if not time_series:
                logger.warning(f"Empty time series for {ticker}")
                return pd.DataFrame()
            
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Rename columns to match expected format
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            # Convert to numeric types
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by date (oldest first) then reverse back to newest first
            df.index = pd.to_datetime(df.index)
            df = df.sort_index(ascending=False)
            
            # Keep last 30 days of data for default analysis
            df = df.head(30)
            
            logger.info(f"Successfully retrieved {len(df)} data points from Alpha Vantage for {ticker}")
            return df
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching stock data from Alpha Vantage for {ticker}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error parsing Alpha Vantage data for {ticker}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return pd.DataFrame()
    
    def _get_stock_data_finnhub(self, ticker: str) -> pd.DataFrame:
        """Fetch stock data from Finnhub as fallback"""
        if not self.finnhub_key:
            logger.warning("Finnhub API key not configured")
            return pd.DataFrame()
        
        try:
            time.sleep(0.2)  # Rate limiting
            url = "https://finnhub.io/api/v1/stock/candle"
            
            # Calculate date range (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            params = {
                'symbol': ticker,
                'resolution': 'D',  # Daily
                'from': int(start_date.timestamp()),
                'to': int(end_date.timestamp()),
                'token': self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('s') == 'no_data':
                logger.warning(f"No data available from Finnhub for {ticker}")
                return pd.DataFrame()
            
            # Parse candlestick data
            if 't' not in data or not data['t']:
                logger.error(f"Unexpected response format from Finnhub for {ticker}")
                return pd.DataFrame()
            
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(data['t'], unit='s'),
                'Open': data['o'],
                'High': data['h'],
                'Low': data['l'],
                'Close': data['c'],
                'Volume': data['v']
            })
            
            df.set_index('timestamp', inplace=True)
            df = df.sort_index(ascending=False)
            
            logger.info(f"Successfully retrieved {len(df)} data points from Finnhub for {ticker}")
            return df
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching stock data from Finnhub for {ticker}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error parsing Finnhub data for {ticker}: {e}")
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
        Get company information from Alpha Vantage with Finnhub fallback
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with company information
        """
        # Try Alpha Vantage first
        company_data = self._get_company_info_alpha_vantage(ticker)
        
        # Fallback to Finnhub if Alpha Vantage fails
        if not company_data or 'error' in company_data:
            if self.finnhub_key:
                logger.warning(f"Alpha Vantage failed for {ticker}, trying Finnhub...")
                company_data = self._get_company_info_finnhub(ticker)
            else:
                company_data = {'ticker': ticker, 'error': 'No API keys configured'}
        
        logger.info(f"Retrieved company info for {ticker}")
        return company_data
    
    def _get_company_info_alpha_vantage(self, ticker: str) -> Dict[str, Any]:
        """Fetch company info from Alpha Vantage OVERVIEW endpoint"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return {}
        
        try:
            time.sleep(0.5)  # Increased delay to avoid rate limits
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'OVERVIEW',
                'symbol': ticker,
                'apikey': self.alpha_vantage_key
            }
            
            logger.debug(f"Requesting Alpha Vantage OVERVIEW for {ticker}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for various error/limit responses
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return {}
            
            if 'Information' in data:
                logger.warning(f"Alpha Vantage rate limit hit: {data['Information']}")
                return {}
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage note: {data['Note']}")
                return {}
            
            if not data or data.get('Symbol') != ticker:
                logger.warning(f"No company data found for {ticker}")
                logger.debug(f"Response: {str(data)[:500]}")
                return {}
            
            # Extract and map key information
            company_data = {
                'ticker': ticker,
                'name': data.get('Name', ''),
                'sector': data.get('Sector', ''),
                'industry': data.get('Industry', ''),
                'market_cap': int(data.get('MarketCapitalization', 0) or 0),
                'employees': int(data.get('FullTimeEmployees', 0) or 0),
                'description': data.get('Description', ''),
                'website': data.get('Website', ''),
                'current_price': float(data.get('AnalystTargetPrice', 0) or 0),
                'previous_close': float(data.get('PreviousClose', 0) or 0),
                'fifty_two_week_high': float(data.get('52WeekHigh', 0) or 0),
                'fifty_two_week_low': float(data.get('52WeekLow', 0) or 0),
                'pe_ratio': float(data.get('TrailingPE', 0) or 0),
                'forward_pe': float(data.get('ForwardPE', 0) or 0),
                'peg_ratio': float(data.get('PEGRatio', 0) or 0),
                'dividend_yield': float(data.get('DividendYield', 0) or 0),
                'beta': float(data.get('Beta', 0) or 0),
                'profit_margins': float(data.get('ProfitMargin', 0) or 0),
                'revenue_growth': float(data.get('RevenuePerShareTTM', 0) or 0),
            }
            
            logger.info(f"Successfully retrieved company info from Alpha Vantage for {ticker}")
            return company_data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching company info from Alpha Vantage for {ticker}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing Alpha Vantage company data for {ticker}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def _get_company_info_finnhub(self, ticker: str) -> Dict[str, Any]:
        """Fetch company info from Finnhub as fallback"""
        if not self.finnhub_key:
            logger.warning("Finnhub API key not configured")
            return {}
        
        try:
            time.sleep(0.2)  # Rate limiting
            url = "https://finnhub.io/api/v1/stock/profile2"
            params = {
                'symbol': ticker,
                'token': self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logger.warning(f"No company data found from Finnhub for {ticker}")
                return {}
            
            company_data = {
                'ticker': ticker,
                'name': data.get('name', ''),
                'sector': data.get('finnhubIndustry', ''),
                'industry': data.get('finnhubIndustry', ''),
                'market_cap': data.get('marketCapitalization', 0) * 1_000_000 if data.get('marketCapitalization') else 0,
                'employees': 0,  # Not available in Finnhub
                'description': '',  # Not available in Finnhub
                'website': data.get('weburl', ''),
                'current_price': 0,  # Use quote endpoint separately if needed
                'previous_close': 0,  # Use quote endpoint separately if needed
                'fifty_two_week_high': 0,
                'fifty_two_week_low': 0,
                'pe_ratio': 0,
                'forward_pe': 0,
                'peg_ratio': 0,
                'dividend_yield': 0,
                'beta': 0,
                'profit_margins': 0,
                'revenue_growth': 0,
            }
            
            logger.info(f"Successfully retrieved company info from Finnhub for {ticker}")
            return company_data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching company info from Finnhub for {ticker}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing Finnhub company data for {ticker}: {e}")
            return {}
    
    def get_financial_statements(self, ticker: str) -> Dict[str, Any]:
        """
        Get financial statements - delegated to FinancialDataCollector
        
        This method is kept for backwards compatibility but returns empty dict.
        Actual financial statements are collected by FinancialDataCollector which uses Alpha Vantage.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Empty dictionary (financial data is collected separately by FinancialDataCollector)
        """
        logger.info(f"Financial statements collection delegated to FinancialDataCollector for {ticker}")
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
