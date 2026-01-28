"""
Configuration Manager
Loads and manages system configuration from YAML and environment variables
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
import os


class Settings(BaseSettings):
    """System settings loaded from environment variables"""
    
    # API Keys
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    alpha_vantage_api_key: Optional[str] = Field(None, alias="ALPHA_VANTAGE_API_KEY")
    finnhub_api_key: Optional[str] = Field(None, alias="FINNHUB_API_KEY")
    newsapi_key: Optional[str] = Field(None, alias="NEWSAPI_KEY")
    
    # Model Configuration
    default_llm_model: str = Field("gpt-4-turbo-preview", alias="DEFAULT_LLM_MODEL")
    local_model_path: str = Field("./models", alias="LOCAL_MODEL_PATH")
    use_local_models: bool = Field(False, alias="USE_LOCAL_MODELS")
    
    # System Configuration
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    max_agent_iterations: int = Field(5, alias="MAX_AGENT_ITERATIONS")
    agent_timeout_seconds: int = Field(300, alias="AGENT_TIMEOUT_SECONDS")
    
    # Directories
    data_cache_dir: str = Field("./data/cache", alias="DATA_CACHE_DIR")
    output_dir: str = Field("./outputs", alias="OUTPUT_DIR")
    log_dir: str = Field("./logs", alias="LOG_DIR")
    
    # Trading Parameters
    default_ticker: str = Field("AAPL", alias="DEFAULT_TICKER")
    risk_threshold: float = Field(0.7, alias="RISK_THRESHOLD")
    confidence_threshold: float = Field(0.6, alias="CONFIDENCE_THRESHOLD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class ConfigManager:
    """Manages configuration from both YAML and environment variables"""
    
    def __init__(self, config_path: Optional[Path] = None):
        # Load environment variables
        load_dotenv()
        
        # Load settings from env
        self.settings = Settings()
        
        # Load YAML configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        self.config_path = config_path
        self.config = self._load_yaml_config()
        
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key (e.g., 'agents.geopolitical_analyst.weight')"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent"""
        return self.get(f"agents.{agent_name}", {})
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all agents"""
        return self.get("agents", {})
    
    @property
    def data_sources(self) -> Dict[str, Any]:
        """Get data sources configuration"""
        return self.get("data_sources", {})
    
    @property
    def model_config(self) -> Dict[str, Any]:
        """Get model configuration"""
        return self.get("models", {})
    
    @property
    def reasoning_config(self) -> Dict[str, Any]:
        """Get reasoning layer configuration"""
        return self.get("reasoning", {})
    
    @property
    def decision_config(self) -> Dict[str, Any]:
        """Get decision layer configuration"""
        return self.get("decision", {})


# Global configuration instance
config = ConfigManager()
