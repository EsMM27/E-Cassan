"""
News Data Collector
Collects and processes news articles related to stocks and markets
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from loguru import logger

from ..config import config
from ..utils import ensure_dir, save_json, calculate_date_range, generate_hash


class NewsDataCollector:
    """Collects news articles from various sources"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = ensure_dir(cache_dir or config.settings.data_cache_dir)
        self.newsapi_key = config.settings.newsapi_key
        self.finnhub_key = config.settings.finnhub_api_key
    
    def get_newsapi_articles(
        self,
        query: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        max_articles: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from NewsAPI
        
        Args:
            query: Search query (e.g., company name or ticker)
            from_date: Start date for articles
            to_date: End date for articles
            max_articles: Maximum number of articles to retrieve
        
        Returns:
            List of article dictionaries
        """
        if not self.newsapi_key:
            logger.warning("NewsAPI key not configured")
            return []
        
        try:
            # Set default date range if not provided
            if not from_date or not to_date:
                from_date, to_date = calculate_date_range(days_back=7)
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'sortBy': 'relevancy',
                'pageSize': min(max_articles, 100),
                'language': 'en',
                'apiKey': self.newsapi_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            # Format articles
            formatted_articles = []
            for article in articles:
                formatted_articles.append({
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'content': article.get('content', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'author': article.get('author', '')
                })
            
            logger.info(f"Retrieved {len(formatted_articles)} articles from NewsAPI for query: {query}")
            return formatted_articles
        
        except Exception as e:
            logger.error(f"Error fetching NewsAPI articles: {e}")
            return []
    
    def get_finnhub_news(
        self,
        ticker: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch company news from Finnhub
        
        Args:
            ticker: Stock ticker symbol
            from_date: Start date
            to_date: End date
        
        Returns:
            List of news articles
        """
        if not self.finnhub_key:
            logger.warning("Finnhub API key not configured")
            return []
        
        try:
            if not from_date or not to_date:
                from_date, to_date = calculate_date_range(days_back=7)
            
            url = "https://finnhub.io/api/v1/company-news"
            params = {
                'symbol': ticker,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'token': self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            articles = response.json()
            
            # Format articles
            formatted_articles = []
            for article in articles:
                formatted_articles.append({
                    'source': article.get('source', 'Finnhub'),
                    'title': article.get('headline', ''),
                    'description': article.get('summary', ''),
                    'content': article.get('summary', ''),
                    'url': article.get('url', ''),
                    'published_at': datetime.fromtimestamp(article.get('datetime', 0)).isoformat(),
                    'category': article.get('category', ''),
                    'image': article.get('image', '')
                })
            
            logger.info(f"Retrieved {len(formatted_articles)} articles from Finnhub for {ticker}")
            return formatted_articles
        
        except Exception as e:
            logger.error(f"Error fetching Finnhub news: {e}")
            return []
    
    def get_yahoo_finance_news(self, ticker: str, max_articles: int = 20) -> List[Dict[str, Any]]:
        """
        Scrape news from Yahoo Finance (fallback method)
        
        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum articles to retrieve
        
        Returns:
            List of news articles
        """
        try:
            url = f"https://finance.yahoo.com/quote/{ticker}/news"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This is a simplified parser - Yahoo's structure may change
            articles = []
            news_items = soup.find_all('div', class_='Ov(h)', limit=max_articles)
            
            for item in news_items:
                title_elem = item.find('h3')
                link_elem = item.find('a')
                
                if title_elem and link_elem:
                    articles.append({
                        'source': 'Yahoo Finance',
                        'title': title_elem.text.strip(),
                        'description': '',
                        'content': '',
                        'url': f"https://finance.yahoo.com{link_elem.get('href', '')}",
                        'published_at': datetime.now().isoformat()
                    })
            
            logger.info(f"Retrieved {len(articles)} articles from Yahoo Finance for {ticker}")
            return articles
        
        except Exception as e:
            logger.error(f"Error scraping Yahoo Finance news: {e}")
            return []
    
    def collect_all_news(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        days_back: int = 7,
        max_per_source: int = 20
    ) -> Dict[str, Any]:
        """
        Collect news from all available sources
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name for broader search
            days_back: Number of days to look back
            max_per_source: Max articles per source
        
        Returns:
            Dictionary with all collected news
        """
        logger.info(f"Collecting news for {ticker}")
        
        from_date, to_date = calculate_date_range(days_back=days_back)
        
        all_articles = []
        
        # Collect from NewsAPI
        if company_name:
            newsapi_articles = self.get_newsapi_articles(
                query=company_name,
                from_date=from_date,
                to_date=to_date,
                max_articles=max_per_source
            )
            all_articles.extend(newsapi_articles)
        
        # Collect from Finnhub
        finnhub_articles = self.get_finnhub_news(
            ticker=ticker,
            from_date=from_date,
            to_date=to_date
        )
        all_articles.extend(finnhub_articles)
        
        # Collect from Yahoo Finance (fallback)
        if len(all_articles) < 10:
            yahoo_articles = self.get_yahoo_finance_news(ticker, max_articles=max_per_source)
            all_articles.extend(yahoo_articles)
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title_hash = generate_hash(article['title'])
            if title_hash not in seen_titles:
                seen_titles.add(title_hash)
                unique_articles.append(article)
        
        result = {
            'ticker': ticker,
            'company_name': company_name,
            'timestamp': datetime.now().isoformat(),
            'date_range': {
                'from': from_date.isoformat(),
                'to': to_date.isoformat()
            },
            'total_articles': len(unique_articles),
            'articles': unique_articles
        }
        
        # Save to cache
        cache_file = self.cache_dir / f"{ticker}_news.json"
        save_json(result, cache_file)
        
        logger.info(f"Collected {len(unique_articles)} unique news articles for {ticker}")
        return result
