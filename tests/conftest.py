"""
Test Configuration and Fixtures
"""

import os
import sys
from pathlib import Path

import pytest

# Keep tests isolated from developer-local .env keys that the current
# settings model does not declare.
os.environ.pop('ANTHROPIC_API_KEY', None)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture
def mock_stock_data():
    """Mock stock data for testing"""
    return {
        'ticker': 'TEST',
        'company_info': {
            'name': 'Test Company',
            'ticker': 'TEST',
            'sector': 'Technology',
            'industry': 'Software',
            'market_cap': 1000000000,
            'current_price': 100.0,
            'previous_close': 99.0,
            'fifty_two_week_high': 120.0,
            'fifty_two_week_low': 80.0,
            'pe_ratio': 25.0,
            'forward_pe': 22.0,
            'beta': 1.2,
            'profit_margins': 0.15,
            'revenue_growth': 0.10
        },
        'price_data': {
            'latest': {
                'Close': 100.0,
                'Volume': 1000000,
                'RSI': 55.0,
                'MACD': 0.5,
                'MACD_Signal': 0.4,
                'SMA_20': 98.0,
                'SMA_50': 95.0
            }
        }
    }


@pytest.fixture
def mock_news_data():
    """Mock news data for testing"""
    return {
        'ticker': 'TEST',
        'total_articles': 5,
        'articles': [
            {
                'title': 'Test Company Reports Strong Earnings',
                'description': 'Company beats expectations',
                'content': 'Test Company announced strong quarterly results...',
                'source': 'Test News',
                'published_at': '2024-01-01T10:00:00',
                'url': 'https://example.com/article1'
            },
            {
                'title': 'Analysts Upgrade Test Company Stock',
                'description': 'Multiple analysts raise price targets',
                'content': 'Several analysts have upgraded...',
                'source': 'Financial Times',
                'published_at': '2024-01-02T14:00:00',
                'url': 'https://example.com/article2'
            }
        ]
    }


@pytest.fixture
def mock_financial_data():
    """Mock financial data for testing"""
    return {
        'ticker': 'TEST',
        'company_overview': {
            'Name': 'Test Company',
            'Exchange': 'NASDAQ',
            'Currency': 'USD',
            'Sector': 'Technology',
            'MarketCapitalization': '1000000000',
            'PERatio': '25.0',
            'EPS': '4.00'
        },
        'earnings': {
            'quarterly_earnings': [
                {
                    'fiscalDateEnding': '2023-12-31',
                    'reportedEPS': '1.20',
                    'estimatedEPS': '1.10',
                    'surprise': '0.10'
                }
            ]
        }
    }


@pytest.fixture
def mock_complete_data(mock_stock_data, mock_news_data, mock_financial_data):
    """Mock complete data package"""
    return {
        'ticker': 'TEST',
        'company_name': 'Test Company',
        'timestamp': '2024-01-01T12:00:00',
        'data': {
            'stock': mock_stock_data,
            'news': mock_news_data,
            'financials': mock_financial_data
        }
    }


@pytest.fixture
def mock_agent_response():
    """Mock agent response"""
    from src.agent_layer.base_agent import AgentResponse
    
    return AgentResponse(
        agent_name='test_agent',
        agent_role='Test Analyst',
        analysis='This is a test analysis',
        recommendation='BUY',
        confidence=0.8,
        reasoning='Strong fundamentals and positive sentiment',
        key_points=['Point 1', 'Point 2', 'Point 3'],
        risks=['Risk 1', 'Risk 2']
    )
