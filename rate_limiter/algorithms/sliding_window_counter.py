"""
Sliding Window Counter Algorithm

This module implements the Sliding Window Counter rate limiting algorithm.
"""

import time
import threading


class SlidingWindowCounter:
    """
    Sliding Window Counter Rate Limiter

    HOW IT WORKS:
    -------------
    A hybrid approach that combines Fixed Window and Sliding Window Log.
    Instead of storing individual timestamps, it uses weighted counters
    from the current and previous windows to estimate the sliding window count.

    The algorithm:
    1. Divide time into fixed windows
    2. Track request count for current window and previous window
    3. Calculate weighted count: (prev_count * weight) + current_count
       where weight = portion of previous window still in sliding window
    4. If weighted count < max_requests, ALLOW
    5. Otherwise, REJECT

    VISUAL REPRESENTATION:
    ----------------------
        Time:     |----1s----|----1s----|
        Window:   [ Previous ][ Current ]
        Count:    [    8     ][    4    ]

        At time t = 0.5s into current window:
        - 50% of previous window is still in sliding window
        - Weighted count = (8 * 0.5) + 4 = 8 requests

        Sliding window covers: [----prev 50%----|----curr 50%----]

    ADVANTAGES:
    -----------
    - No boundary problem (smooths across window edges)
    - Memory efficient (only 2 counters vs. storing all timestamps)
    - Good approximation of true sliding window
    - Fast O(1) operations

    DISADVANTAGES:
    --------------
    - Approximation, not exact (can slightly over/under count)
    - More complex than Fixed Window
    - Still has some window boundary effects (though reduced)

    TYPICAL USE CASES:
    ------------------
    - High-throughput API rate limiting
    - Distributed systems (easy to aggregate counters)
    - Redis-based rate limiting
    - When you need accuracy + memory efficiency
    - Cloud load balancers
    """

    def __init__(self, max_requests: int, window_seconds: float):
        """
        Initialize the Sliding Window Counter.

        Args:
            max_requests: Maximum number of requests allowed per window.
            window_seconds: Duration of each time window in seconds.

        Example:
            # Allow 100 requests per minute with sliding window
            limiter = SlidingWindowCounter(max_requests=100, window_seconds=60)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        # Counters for current and previous windows
        self.current_count = 0
        self.previous_count = 0

        # Track window timing
        self.current_window_start = time.time()
        self._lock = threading.Lock()

    def _update_windows(self):
        """
        Update window counters based on current time.

        Determines which window we're in and:
        - If in a new window, shift current to previous and reset current
        - If skipped multiple windows, reset both counters
        """
        current_time = time.time()
        elapsed = current_time - self.current_window_start

        # Check how many windows have passed
        windows_passed = int(elapsed / self.window_seconds)

        if windows_passed == 0:
            # Still in the same window, no update needed
            return
        elif windows_passed == 1:
            # Moved to next window: current becomes previous
            self.previous_count = self.current_count
            self.current_count = 0
            self.current_window_start += self.window_seconds
        else:
            # Skipped multiple windows: reset everything
            # (no requests in the sliding window from that long ago)
            self.previous_count = 0
            self.current_count = 0
            self.current_window_start = current_time

    def _get_weighted_count(self) -> float:
        """
        Calculate the weighted request count for the sliding window.

        The weight represents how much of the previous window
        is still within the current sliding window.

        Returns:
            Weighted count combining previous and current window counts.
        """
        current_time = time.time()
        elapsed_in_current = current_time - self.current_window_start

        # Calculate what portion of the previous window is still in our
        # sliding window. If we're 30% into current window, then 70% of
        # previous window is still in the sliding window.
        weight = 1.0 - (elapsed_in_current / self.window_seconds)
        weight = max(0.0, min(1.0, weight))  # Clamp between 0 and 1

        # Weighted count = (previous * weight) + current
        return (self.previous_count * weight) + self.current_count

    def allow_request(self) -> bool:
        """
        Check if a request should be allowed.

        This method:
        1. Updates window counters
        2. Calculates weighted count for sliding window
        3. If weighted count < max_requests, ALLOW and increment current
        4. Otherwise, REJECT

        Returns:
            True if the request is allowed, False if rejected.

        Example:
            limiter = SlidingWindowCounter(max_requests=5, window_seconds=1)
            limiter.allow_request()  # True
            limiter.allow_request()  # True
            # ... after 5 requests in weighted window ...
            limiter.allow_request()  # False
        """
        with self._lock:
            self._update_windows()

            weighted_count = self._get_weighted_count()

            if weighted_count < self.max_requests:
                self.current_count += 1
                return True
            return False

    def get_weighted_count(self) -> float:
        """
        Get the current weighted request count (for debugging/demo).

        Returns:
            The weighted count representing requests in sliding window.
        """
        with self._lock:
            self._update_windows()
            return self._get_weighted_count()

    def get_remaining(self) -> int:
        """
        Get the approximate number of remaining requests allowed.

        Returns:
            Approximate remaining requests (may be fractional internally).
        """
        with self._lock:
            self._update_windows()
            weighted_count = self._get_weighted_count()
            return max(0, int(self.max_requests - weighted_count))

    def get_window_info(self) -> dict:
        """
        Get detailed window information (for debugging/demo).

        Returns:
            Dictionary with window statistics.
        """
        with self._lock:
            self._update_windows()
            weighted_count = self._get_weighted_count()
            return {
                "previous_count": self.previous_count,
                "current_count": self.current_count,
                "weighted_count": weighted_count,
                "max_requests": self.max_requests,
                "remaining": max(0, int(self.max_requests - weighted_count)),
            }
