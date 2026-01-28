"""
Utility functions for the E-Cassan system
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
from loguru import logger
import hashlib


def ensure_dir(directory: Path) -> Path:
    """Ensure directory exists, create if it doesn't"""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_json(data: Dict[str, Any], filepath: Path, indent: int = 2) -> None:
    """Save data to JSON file"""
    filepath = Path(filepath)
    ensure_dir(filepath.parent)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
    
    logger.info(f"Saved JSON to {filepath}")


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load data from JSON file"""
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_timestamp(format: str = "%Y%m%d_%H%M%S") -> str:
    """Get current timestamp as formatted string"""
    return datetime.now().strftime(format)


def calculate_date_range(days_back: int = 7) -> tuple[datetime, datetime]:
    """Calculate date range from today going back specified days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date


def generate_hash(text: str) -> str:
    """Generate MD5 hash of text for caching purposes"""
    return hashlib.md5(text.encode()).hexdigest()


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """Format float as percentage string"""
    return f"{value * 100:.{decimal_places}f}%"


def parse_signal(signal: str) -> tuple[str, float]:
    """
    Parse trading signal and confidence
    Example: "BUY (0.85)" -> ("BUY", 0.85)
    """
    parts = signal.split('(')
    action = parts[0].strip()
    
    if len(parts) > 1:
        confidence = float(parts[1].rstrip(')').strip())
    else:
        confidence = 0.0
    
    return action, confidence


def validate_ticker(ticker: str) -> bool:
    """Basic validation for stock ticker symbol"""
    if not ticker:
        return False
    
    # Basic rules: uppercase letters, 1-5 characters
    return ticker.isalpha() and 1 <= len(ticker) <= 5


class Timer:
    """Simple context manager for timing operations"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        logger.info(f"{self.name} started")
        return self
    
    def __exit__(self, *args):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"{self.name} completed in {duration:.2f} seconds")
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
