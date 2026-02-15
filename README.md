# E-Cassan: AI-Driven Market Sentiment and Trading Agents

## Overview

E-Cassan is an advanced AI-driven system that autonomously analyzes financial markets by interpreting company news, earnings data, and global geopolitical events to produce transparent, evidence-based trading indicators. The system uses a multi-agent architecture where specialized AI agents collaborate, debate, and reach consensus on investment decisions.

## Key Features

- **Multi-Agent Architecture**: Four specialized agents (Geopolitical, Fundamental, Technical, Sentiment)
- **Transparent Decision Making**: Full audit trail of reasoning and debates
- **Comprehensive Data Integration**: Combines structured (prices, financials) and unstructured data (news, sentiment)
- **Explainable Signals**: Clear cause-and-effect reasoning for each recommendation
- **Modular Design**: Layered architecture (Data → Agent → Reasoning → Decision)

## Architecture

The system consists of four main layers:

### 1. Data Layer
- **Stock Data Collector**: Price data, technical indicators, company information
- **News Data Collector**: News articles from multiple sources 
- **Financial Data Collector**: Earnings reports, financial statements, fundamentals
- **Data Pipeline**: Cleans and formats data for agent consumption

### 2. Agent Layer
- **Geopolitical Agent**: Analyzes global events and their market impact
- **Fundamental Agent**: Evaluates company financials and business model
- **Technical Agent**: Analyzes price movements and technical indicators
- **Sentiment Agent**: Extracts sentiment using FinBERT and LLM analysis

### 3. Reasoning Layer
- **Debate Manager**: Orchestrates multi-round debates between agents
- **Consensus Builder**: Aggregates recommendations using weighted voting
- **Reasoning Logger**: Maintains audit trail of all reasoning

### 4. Decision Layer
- **Signal Generator**: Converts consensus into actionable trading signals
- **Decision Logger**: Logs all signals for performance tracking

## Installation

### Prerequisites
- Python 3.10 or higher
- 32-64GB RAM (recommended for local LLM models)
- GPU with CUDA support (optional, for faster sentiment analysis)

### Setup

1. **Clone the repository**
```powershell
git clone https://github.com/EsMM27/E-Cassan.git
cd E-Cassan
```

2. **Create virtual environment**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. **Install dependencies**
```powershell
pip install -r requirements.txt
```

4. **Configure environment**
```powershell
cp .env.example .env
# Edit .env with your API keys
```

### Required API Keys

Add the following to your `.env` file:

```ini
# LLM APIs
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Financial Data APIs
ALPHA_VANTAGE_API_KEY=your_alphavantage_key
FINNHUB_API_KEY=your_finnhub_key
NEWSAPI_KEY=your_newsapi_key
```

## Usage

### Quick Start

Analyze a single stock:

```powershell
python -m src.main TSLA
```

### Python API

```python
from src.main import ECassanSystem

# Initialize system
system = ECassanSystem(use_finbert=True)

# Analyze a stock
result = system.analyze_stock('AAPL')

# Get formatted signal
signal_text = system.quick_analysis('AAPL')
print(signal_text)
```

### Batch Analysis

Analyze multiple stocks:

```python
from src.main import ECassanSystem

system = ECassanSystem()
results = system.batch_analysis(['AAPL', 'MSFT', 'GOOGL'])
```

## Configuration

Edit `config/config.yaml` to customize:

- Agent weights and roles
- LLM model selection
- Data source preferences
- Debate parameters
- Signal thresholds

## Output

The system generates:

1. **Trading Signal** (JSON)
2. **Formatted Report** (TXT)
3. **Debate Log** (JSON)
4. **Signal History** (JSONL)

## Testing

Run the test suite:

```powershell
pytest
pytest --cov=src --cov-report=html
```

## Project Structure

```
E-Cassan/
├── src/
│   ├── data_layer/          # Data collection and processing
│   ├── agent_layer/         # AI agents
│   ├── reasoning_layer/     # Debate and consensus
│   ├── decision_layer/      # Signal generation
│   ├── config.py            # Configuration management
│   ├── utils.py             # Utility functions
│   └── main.py              # Main orchestrator
├── tests/                   # Test suite
├── config/                  # Configuration files
├── data/                    # Data cache
├── logs/                    # System logs (Created on run)
├── outputs/                 # Generated signals and reports (Created on run)
├── requirements.txt         # Python dependencies
└── README.md
```

## Contact

**Edgar Malevic**  
Student ID: L00148202  
Email: L00148202@atu.ie  
GitHub: [@EsMM27](https://github.com/EsMM27)

---

**Disclaimer**: This system is for educational and research purposes only. It does not constitute financial advice.