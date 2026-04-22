"""
Integration tests
"""

import pytest


class TestSystemIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.integration
    def test_complete_analysis_flow(self):
        """Test complete analysis flow when all external API keys are configured"""
        from src.config import config
        from src.main import ECassanSystem

        required_keys = {
            'OPENAI_API_KEY': config.settings.openai_api_key,
            'ALPHA_VANTAGE_API_KEY': config.settings.alpha_vantage_api_key,
            'FINNHUB_API_KEY': config.settings.finnhub_api_key,
            'NEWSAPI_KEY': config.settings.newsapi_key,
        }

        missing_keys = [name for name, value in required_keys.items() if not value]
        if missing_keys:
            pytest.skip(f"Missing required API keys: {', '.join(missing_keys)}")
        
        system = ECassanSystem(log_level='WARNING')
        
        result = system.analyze_stock('AAPL', save_outputs=False)

        assert 'trading_signal' in result
        assert result['ticker'] == 'AAPL'
        assert result['trading_signal']['ticker'] == 'AAPL'
        assert result['trading_signal']['signal'] is not None
        assert result['consensus_report'] is not None
        assert result['debate_result'] is not None
    
    def test_system_initialization(self):
        """Test system initialization"""
        from src.main import ECassanSystem
        
        system = ECassanSystem(log_level='WARNING')
        
        assert system.data_manager is not None
        assert system.data_pipeline is not None
        assert len(system.agents) == 4
        assert system.debate_manager is not None
        assert system.consensus_builder is not None
        assert system.signal_generator is not None
        assert system.decision_logger is not None
