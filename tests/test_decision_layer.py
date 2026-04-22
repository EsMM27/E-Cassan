"""
Tests for Decision Layer
"""

import pytest
from src.decision_layer.signal_generator import SignalGenerator, TradingSignal
from src.decision_layer.decision_logger import DecisionLogger


class TestSignalGenerator:
    """Tests for SignalGenerator"""
    
    def test_determine_signal_strength_strong_buy(self):
        """Test strong buy signal determination"""
        generator = SignalGenerator()
        
        signal = generator.determine_signal_strength('BUY', 0.9, 0.8)
        assert signal == 'STRONG_BUY'
    
    def test_determine_signal_strength_buy(self):
        """Test buy signal determination"""
        generator = SignalGenerator()
        
        signal = generator.determine_signal_strength('BUY', 0.7, 0.6)
        assert signal == 'BUY'
    
    def test_determine_signal_strength_hold(self):
        """Test hold signal determination"""
        generator = SignalGenerator()
        
        signal = generator.determine_signal_strength('HOLD', 0.5, 0.5)
        assert signal == 'HOLD'
    
    def test_extract_consensus_price_levels_buy(self):
        """Test extracting consensus price levels for BUY"""
        generator = SignalGenerator()
        
        consensus_report = {
            'consensus': {
                'recommendation': 'BUY',
                'confidence': 0.8,
                'price_target': 115.0,
                'stop_loss': 95.0
            }
        }
        
        target, stop = generator.extract_consensus_price_levels(consensus_report, 100.0)
        
        assert target == 115.0
        assert stop == 95.0
    
    def test_determine_time_horizon(self):
        """Test time horizon determination"""
        generator = SignalGenerator()
        
        # High confidence = long term
        report1 = {'consensus': {'confidence': 0.9}}
        horizon1 = generator.determine_time_horizon(report1)
        assert horizon1 == 'long_term'
        
        # Medium confidence = medium term
        report2 = {'consensus': {'confidence': 0.7}}
        horizon2 = generator.determine_time_horizon(report2)
        assert horizon2 == 'medium_term'
        
        # Low confidence = short term
        report3 = {'consensus': {'confidence': 0.4}}
        horizon3 = generator.determine_time_horizon(report3)
        assert horizon3 == 'short_term'


class TestTradingSignal:
    """Tests for TradingSignal"""
    
    def test_trading_signal_creation(self):
        """Test creating trading signal"""
        signal = TradingSignal(
            ticker='TEST',
            company_name='Test Company',
            signal='BUY',
            confidence=0.8,
            consensus_level=0.75,
            agent_breakdown={'BUY': 3, 'HOLD': 1, 'SELL': 0},
            weighted_scores={'BUY': 0.7, 'HOLD': 0.2, 'SELL': 0.1},
            key_factors=['Factor 1', 'Factor 2'],
            risks=['Risk 1'],
            agent_consensus='Strong buy consensus',
            total_agents=4,
            debate_rounds=2,
            methodology='weighted',
            reasoning_summary='Test reasoning',
            individual_agent_views=[]
        )
        
        assert signal.ticker == 'TEST'
        assert signal.signal == 'BUY'
        assert signal.confidence == 0.8
        assert signal.total_agents == 4
    
    def test_signal_validation(self):
        """Test signal validation"""
        # Confidence must be between 0 and 1
        with pytest.raises(ValueError):
            TradingSignal(
                ticker='TEST',
                company_name='Test',
                signal='BUY',
                confidence=1.5,  # Invalid
                consensus_level=0.7,
                agent_breakdown={},
                weighted_scores={},
                key_factors=[],
                risks=[],
                agent_consensus='',
                total_agents=0,
                debate_rounds=0,
                methodology='weighted',
                reasoning_summary='',
                individual_agent_views=[]
            )


class TestDecisionLogger:
    """Tests for DecisionLogger output artifacts"""

    @staticmethod
    def _build_signal() -> TradingSignal:
        return TradingSignal(
            ticker='TEST',
            company_name='Test Company',
            signal='BUY',
            confidence=0.8,
            consensus_level=0.75,
            price_target=110.0,
            stop_loss=95.0,
            time_horizon='medium_term',
            agent_breakdown={'BUY': 3, 'HOLD': 1, 'SELL': 0},
            weighted_scores={'BUY': 0.7, 'HOLD': 0.2, 'SELL': 0.1},
            key_factors=['Strong earnings', 'Positive momentum'],
            risks=['Macro volatility'],
            agent_consensus='Majority buy consensus',
            total_agents=4,
            debate_rounds=2,
            methodology='weighted',
            reasoning_summary='Balanced bullish setup',
            individual_agent_views=[]
        )

    def test_log_signal_creates_json_file(self, tmp_path):
        """Test signal JSON artifact is created in outputs/signals"""
        decision_logger = DecisionLogger(output_dir=str(tmp_path))
        signal = self._build_signal()

        file_path = decision_logger.log_signal(signal)

        assert file_path.exists()
        assert file_path.suffix == '.json'
        assert file_path.parent.name == 'signals'

    def test_log_formatted_signal_creates_txt_report(self, tmp_path):
        """Test formatted text report is created in outputs/reports"""
        decision_logger = DecisionLogger(output_dir=str(tmp_path))
        signal = self._build_signal()
        report_text = 'TEST REPORT\nSignal: BUY\nConfidence: 0.80'

        report_path = decision_logger.log_formatted_signal(signal, report_text)

        assert report_path.exists()
        assert report_path.suffix == '.txt'
        assert report_path.parent.name == 'reports'
        assert report_path.read_text(encoding='utf-8') == report_text

    def test_append_to_history_writes_jsonl_audit_trail(self, tmp_path):
        """Test summary entries are appended to signal history JSONL"""
        decision_logger = DecisionLogger(output_dir=str(tmp_path))
        signal = self._build_signal()

        decision_logger.append_to_history(signal)

        history_file = tmp_path / 'signal_history.jsonl'
        assert history_file.exists()

        history = decision_logger.get_signal_history(ticker='TEST', limit=10)
        assert len(history) == 1
        assert history[0]['ticker'] == 'TEST'
        assert history[0]['signal'] == 'BUY'
