"""
Rate Limiter Package

A collection of rate limiting algorithms for educational purposes.
Each algorithm demonstrates different approaches to controlling request rates.
"""

from .algorithms.token_bucket import TokenBucket
from .algorithms.leaky_bucket import LeakyBucket
from .algorithms.fixed_window_counter import FixedWindowCounter
from .algorithms.sliding_window_log import SlidingWindowLog
from .algorithms.sliding_window_counter import SlidingWindowCounter

__all__ = [
    "TokenBucket",
    "LeakyBucket",
    "FixedWindowCounter",
    "SlidingWindowLog",
    "SlidingWindowCounter",
]

__version__ = "1.0.0"
