import pytest
from src.data_layer.data_pipeline import DataPipeline
from src.data_layer.data_ingestion import DataIngestionManager


class TestDataPipeline:
    """Tests for DataPipeline"""
    
    def test_clean_text(self):
        """Test text cleaning"""
        pipeline = DataPipeline()
        
        # Test basic cleaning
        text = "  This  is   a   test  "
        cleaned = pipeline.clean_text(text)
        assert cleaned == "This is a test"
        
        # Test truncation
        long_text = "a" * 6000
        cleaned = pipeline.clean_text(long_text, max_length=1000)
        assert len(cleaned) <= 1000
    
    def test_format_stock_summary(self, mock_stock_data):
        """Test stock summary formatting"""
        pipeline = DataPipeline()
        summary = pipeline.format_stock_summary(mock_stock_data)
        
        assert 'Test Company' in summary
        assert 'TEST' in summary
        assert 'Current Price' in summary
        assert 'P/E Ratio' in summary
    
    def test_format_news_summary(self, mock_news_data):
        """Test news summary formatting"""
        pipeline = DataPipeline()
        summary = pipeline.format_news_summary(mock_news_data)
        
        assert 'News Summary' in summary
        assert 'Strong Earnings' in summary
        assert 'Total Articles: 5' in summary
    
    def test_extract_key_metrics(self, mock_stock_data):
        """Test key metrics extraction"""
        pipeline = DataPipeline()
        metrics = pipeline.extract_key_metrics(mock_stock_data)
        
        assert metrics['current_price'] == 100.0
        assert metrics['pe_ratio'] == 25.0
        assert metrics['rsi'] == 55.0
        assert 'sma_20' in metrics


class TestDataIngestionManager:
    """Tests for DataIngestionManager"""

    def test_ingest_all_data_creates_and_reuses_cache(self, tmp_path, monkeypatch):
        """Test complete dataset cache is created and reused on repeated calls"""
        manager = DataIngestionManager(cache_dir=str(tmp_path))

        call_counts = {'stock': 0, 'news': 0, 'financials': 0}

        def stock_stub(ticker, period='1mo'):
            call_counts['stock'] += 1
            return {
                'ticker': ticker,
                'company_info': {'name': 'Test Company'},
                'price_data': {'latest': {'Close': 100.0}}
            }

        def news_stub(ticker, company_name=None, days_back=7):
            call_counts['news'] += 1
            return {'ticker': ticker, 'total_articles': 1, 'articles': []}

        def financials_stub(ticker):
            call_counts['financials'] += 1
            return {'ticker': ticker, 'company_overview': {}}

        monkeypatch.setattr(manager.stock_collector, 'collect_complete_stock_data', stock_stub)
        monkeypatch.setattr(manager.news_collector, 'collect_all_news', news_stub)
        monkeypatch.setattr(manager.financial_collector, 'collect_complete_financials', financials_stub)

        first_result = manager.ingest_all_data('TEST')

        cache_file = tmp_path / 'TEST_complete_data.json'
        assert cache_file.exists()
        assert call_counts == {'stock': 1, 'news': 1, 'financials': 1}

        def fail_if_called(*args, **kwargs):
            raise AssertionError('Collector should not be called when cache exists')

        monkeypatch.setattr(manager.stock_collector, 'collect_complete_stock_data', fail_if_called)
        monkeypatch.setattr(manager.news_collector, 'collect_all_news', fail_if_called)
        monkeypatch.setattr(manager.financial_collector, 'collect_complete_financials', fail_if_called)

        second_result = manager.ingest_all_data('TEST')

        assert second_result == first_result
