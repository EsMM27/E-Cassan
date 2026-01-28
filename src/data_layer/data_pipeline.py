"""
Data Pipeline
Processes and cleans raw data for agent consumption
"""

from typing import Dict, Any, List
import pandas as pd
from datetime import datetime
from loguru import logger

from ..config import config
from ..utils import truncate_text


class DataPipeline:
    """Processes and formats data for agent consumption"""
    
    def __init__(self):
        self.config = config
    
    def clean_text(self, text: str, max_length: int = 5000) -> str:
        """
        Clean and normalize text data
        
        Args:
            text: Raw text
            max_length: Maximum text length
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Truncate if too long
        text = truncate_text(text, max_length)
        
        return text
    
    def format_stock_summary(self, stock_data: Dict[str, Any]) -> str:
        """
        Format stock data into readable summary
        
        Args:
            stock_data: Raw stock data
        
        Returns:
            Formatted summary string
        """
        try:
            company_info = stock_data.get('company_info', {})
            price_data = stock_data.get('price_data', {}).get('latest', {})
            
            summary = f"""
# Stock Summary: {company_info.get('name', 'Unknown')} ({company_info.get('ticker', 'N/A')})

## Company Information
- Sector: {company_info.get('sector', 'N/A')}
- Industry: {company_info.get('industry', 'N/A')}
- Market Cap: ${company_info.get('market_cap', 0):,.0f}
- Employees: {company_info.get('employees', 0):,}

## Current Price Information
- Current Price: ${company_info.get('current_price', 0):.2f}
- Previous Close: ${company_info.get('previous_close', 0):.2f}
- 52 Week High: ${company_info.get('fifty_two_week_high', 0):.2f}
- 52 Week Low: ${company_info.get('fifty_two_week_low', 0):.2f}

## Valuation Metrics
- P/E Ratio: {company_info.get('pe_ratio', 0):.2f}
- Forward P/E: {company_info.get('forward_pe', 0):.2f}
- PEG Ratio: {company_info.get('peg_ratio', 0):.2f}
- Beta: {company_info.get('beta', 0):.2f}

## Financial Health
- Profit Margins: {company_info.get('profit_margins', 0):.2%}
- Revenue Growth: {company_info.get('revenue_growth', 0):.2%}
- Dividend Yield: {company_info.get('dividend_yield', 0):.2%}

## Technical Indicators (Latest)
- RSI: {price_data.get('RSI', 0):.2f}
- MACD: {price_data.get('MACD', 0):.4f}
- MACD Signal: {price_data.get('MACD_Signal', 0):.4f}
- SMA 20: ${price_data.get('SMA_20', 0):.2f}
- SMA 50: ${price_data.get('SMA_50', 0):.2f}

## Business Description
{self.clean_text(company_info.get('description', 'No description available'), max_length=500)}
"""
            return summary.strip()
        
        except Exception as e:
            logger.error(f"Error formatting stock summary: {e}")
            return "Error formatting stock data"
    
    def format_news_summary(self, news_data: Dict[str, Any], max_articles: int = 10) -> str:
        """
        Format news articles into readable summary
        
        Args:
            news_data: Raw news data
            max_articles: Maximum number of articles to include
        
        Returns:
            Formatted summary string
        """
        try:
            articles = news_data.get('articles', [])[:max_articles]
            
            summary = f"""
# News Summary: {news_data.get('company_name', news_data.get('ticker', 'Unknown'))}

Total Articles: {news_data.get('total_articles', 0)}
Date Range: {news_data.get('date_range', {}).get('from', 'N/A')} to {news_data.get('date_range', {}).get('to', 'N/A')}

## Recent Articles

"""
            
            for i, article in enumerate(articles, 1):
                summary += f"""
### Article {i}: {article.get('title', 'No Title')}
- Source: {article.get('source', 'Unknown')}
- Published: {article.get('published_at', 'N/A')}
- URL: {article.get('url', 'N/A')}

{self.clean_text(article.get('description', article.get('content', 'No content')), max_length=300)}

---
"""
            
            return summary.strip()
        
        except Exception as e:
            logger.error(f"Error formatting news summary: {e}")
            return "Error formatting news data"
    
    def format_financial_summary(self, financial_data: Dict[str, Any]) -> str:
        """
        Format financial data into readable summary
        
        Args:
            financial_data: Raw financial data
        
        Returns:
            Formatted summary string
        """
        try:
            overview = financial_data.get('company_overview', {})
            earnings = financial_data.get('earnings', {})
            
            summary = f"""
# Financial Summary: {overview.get('Name', financial_data.get('ticker', 'Unknown'))}

## Company Overview
- Exchange: {overview.get('Exchange', 'N/A')}
- Currency: {overview.get('Currency', 'N/A')}
- Country: {overview.get('Country', 'N/A')}
- Sector: {overview.get('Sector', 'N/A')}
- Industry: {overview.get('Industry', 'N/A')}

## Key Financials
- Market Capitalization: {overview.get('MarketCapitalization', 'N/A')}
- EBITDA: {overview.get('EBITDA', 'N/A')}
- PE Ratio: {overview.get('PERatio', 'N/A')}
- PEG Ratio: {overview.get('PEGRatio', 'N/A')}
- EPS: {overview.get('EPS', 'N/A')}
- Revenue Per Share: {overview.get('RevenuePerShareTTM', 'N/A')}
- Profit Margin: {overview.get('ProfitMargin', 'N/A')}
- Operating Margin: {overview.get('OperatingMarginTTM', 'N/A')}

## Growth Metrics
- Revenue Growth (YoY): {overview.get('QuarterlyRevenueGrowthYOY', 'N/A')}
- Earnings Growth (YoY): {overview.get('QuarterlyEarningsGrowthYOY', 'N/A')}

## Analyst Targets
- Analyst Target Price: {overview.get('AnalystTargetPrice', 'N/A')}
- 52 Week High: {overview.get('52WeekHigh', 'N/A')}
- 52 Week Low: {overview.get('52WeekLow', 'N/A')}

## Recent Earnings
"""
            
            # Add quarterly earnings if available
            quarterly_earnings = earnings.get('quarterly_earnings', [])
            if quarterly_earnings:
                summary += "\n### Quarterly Earnings (Most Recent)\n"
                for i, qtr in enumerate(quarterly_earnings[:4], 1):
                    summary += f"\n**Q{i}** ({qtr.get('fiscalDateEnding', 'N/A')})\n"
                    summary += f"- Reported EPS: {qtr.get('reportedEPS', 'N/A')}\n"
                    summary += f"- Estimated EPS: {qtr.get('estimatedEPS', 'N/A')}\n"
                    summary += f"- Surprise: {qtr.get('surprise', 'N/A')}\n"
            
            return summary.strip()
        
        except Exception as e:
            logger.error(f"Error formatting financial summary: {e}")
            return "Error formatting financial data"
    
    def prepare_agent_input(self, raw_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare formatted data for agent consumption
        
        Args:
            raw_data: Raw data from ingestion
        
        Returns:
            Dictionary with formatted data sections
        """
        logger.info(f"Preparing agent input for {raw_data.get('ticker', 'Unknown')}")
        
        stock_data = raw_data.get('data', {}).get('stock', {})
        news_data = raw_data.get('data', {}).get('news', {})
        financial_data = raw_data.get('data', {}).get('financials', {})
        
        agent_input = {
            'ticker': raw_data.get('ticker', 'Unknown'),
            'company_name': raw_data.get('company_name', 'Unknown'),
            'timestamp': raw_data.get('timestamp', datetime.now().isoformat()),
            'stock_summary': self.format_stock_summary(stock_data),
            'news_summary': self.format_news_summary(news_data),
            'financial_summary': self.format_financial_summary(financial_data),
            'raw_data': raw_data  # Keep raw data for reference
        }
        
        logger.info("Agent input prepared successfully")
        return agent_input
    
    def extract_key_metrics(self, stock_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract key numerical metrics for quantitative analysis
        
        Args:
            stock_data: Stock data dictionary
        
        Returns:
            Dictionary of key metrics
        """
        company_info = stock_data.get('company_info', {})
        price_data = stock_data.get('price_data', {}).get('latest', {})
        
        return {
            'current_price': company_info.get('current_price', 0),
            'pe_ratio': company_info.get('pe_ratio', 0),
            'forward_pe': company_info.get('forward_pe', 0),
            'peg_ratio': company_info.get('peg_ratio', 0),
            'beta': company_info.get('beta', 0),
            'profit_margins': company_info.get('profit_margins', 0),
            'revenue_growth': company_info.get('revenue_growth', 0),
            'rsi': price_data.get('RSI', 50),
            'macd': price_data.get('MACD', 0),
            'sma_20': price_data.get('SMA_20', 0),
            'sma_50': price_data.get('SMA_50', 0),
        }
