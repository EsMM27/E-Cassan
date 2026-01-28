"""
Reasoning Layer Package
Handles inter-agent communication, debate, and consensus building
"""

from .debate_manager import DebateManager
from .consensus_builder import ConsensusBuilder
from .reasoning_logger import ReasoningLogger

__all__ = [
    'DebateManager',
    'ConsensusBuilder',
    'ReasoningLogger'
]
