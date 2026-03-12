"""
Token Bucket Algorithm

This module implements the Token Bucket rate limiting algorithm.
"""

import time
import threading


class TokenBucket:
    """
    Token Bucket Rate Limiter

    HOW IT WORKS:
    -------------
    Imagine a bucket that can hold a maximum number of tokens. Tokens are added
    to the bucket at a fixed rate (refill_rate tokens per second). When a request
    arrives, it tries to consume one token from the bucket:
    
    - If tokens are available, the request is ALLOWED and one token is removed.
    - If no tokens are available, the request is REJECTED.
    
    The bucket starts full (with max_tokens tokens).

    VISUAL REPRESENTATION:
    ----------------------
        Tokens added continuously
              ↓
        ┌─────────────┐
        │  BUCKET     │  ← Holds up to max_tokens
        │  [●●●○○]    │  ← Current tokens (3/5)
        └─────────────┘
              ↓
        Request consumes 1 token

    ADVANTAGES:
    -----------
    - Allows bursting: Can handle sudden spikes up to max_tokens
    - Smooth rate limiting over time
    - Simple to understand and implement
    - Tokens accumulate during idle periods (up to max)

    DISADVANTAGES:
    --------------
    - Can allow bursts that might overwhelm downstream systems
    - Requires tracking token count and last refill time
    - Not as strict as some other algorithms

    TYPICAL USE CASES:
    ------------------
    - API rate limiting with burst allowance
    - Network traffic shaping
    - Gaming: action cooldowns with stored charges
    - Cloud services: allowing occasional burst usage
    """

    def __init__(self, max_tokens: int, refill_rate: float):
        """
        Initialize the Token Bucket.

        Args:
            max_tokens: Maximum number of tokens the bucket can hold.
                       This is also the maximum burst size.
            refill_rate: Number of tokens added per second.
                        Controls the sustained request rate.

        Example:
            # Allow 10 requests per second, with burst up to 20
            bucket = TokenBucket(max_tokens=20, refill_rate=10)
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = max_tokens  # Start with a full bucket
        self.last_refill_time = time.time()
        self._lock = threading.Lock()  # Thread safety

    def _refill(self):
        """
        Refill tokens based on elapsed time.

        Calculates how many tokens should be added based on the time
        elapsed since the last refill. Tokens are added proportionally
        to the elapsed time.
        """
        current_time = time.time()
        elapsed = current_time - self.last_refill_time

        # Calculate tokens to add based on elapsed time
        tokens_to_add = elapsed * self.refill_rate

        # Add tokens but don't exceed max capacity
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill_time = current_time

    def allow_request(self) -> bool:
        """
        Check if a request should be allowed.

        This method:
        1. Refills tokens based on elapsed time
        2. Checks if at least one token is available
        3. If yes, consumes one token and returns True
        4. If no, returns False (request rejected)

        Returns:
            True if the request is allowed, False if rejected.

        Example:
            bucket = TokenBucket(max_tokens=5, refill_rate=1)
            bucket.allow_request()  # True (5 -> 4 tokens)
            bucket.allow_request()  # True (4 -> 3 tokens)
        """
        with self._lock:  # Thread-safe operation
            self._refill()

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    def get_tokens(self) -> float:
        """
        Get the current number of tokens (for debugging/demo).

        Returns:
            Current token count (may be fractional).
        """
        with self._lock:
            self._refill()
            return self.tokens
