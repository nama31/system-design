"""
Sliding Window Log Algorithm

This module implements the Sliding Window Log rate limiting algorithm.
"""

import time
import threading
from collections import deque


class SlidingWindowLog:
    """
    Sliding Window Log Rate Limiter

    HOW IT WORKS:
    -------------
    Maintain a log (list) of timestamps for all requests within the window.
    When a request arrives:

    1. Remove all timestamps older than (current_time - window_size)
    2. Count the remaining timestamps
    3. If count < max_requests, ALLOW and add current timestamp
    4. If count >= max_requests, REJECT

    VISUAL REPRESENTATION:
    ----------------------
        Window slides with time:

        Time: ----|----|----|----|----|---->
                  t-3  t-2  t-1   t   t+1

        Log at time t: [t-2.5, t-1.8, t-0.5]  (3 requests in window)
                       ↑___________________↑
                       Window: [t-3, t]

        As time moves, old entries fall out of the window

    ADVANTAGES:
    -----------
    - No boundary problem (unlike Fixed Window)
    - Precise rate limiting
    - Smooth request distribution
    - Accurate tracking of request rate

    DISADVANTAGES:
    --------------
    - Memory intensive: stores timestamp for every request
    - Can be slow with high request volumes (O(n) cleanup)
    - Not suitable for high-throughput systems
    - Requires storing individual request records

    TYPICAL USE CASES:
    ------------------
    - Low-volume API rate limiting
    - Security: login attempt limiting
    - When precise rate limiting is required
    - Systems where memory is not a concern
    - Audit logging with rate limiting
    """

    def __init__(self, max_requests: int, window_seconds: float):
        """
        Initialize the Sliding Window Log.

        Args:
            max_requests: Maximum number of requests allowed in the window.
            window_seconds: Size of the sliding window in seconds.

        Example:
            # Allow 10 requests per 60 seconds
            limiter = SlidingWindowLog(max_requests=10, window_seconds=60)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.log = deque()  # Stores timestamps of requests
        self._lock = threading.Lock()

    def _cleanup_old_entries(self):
        """
        Remove timestamps that are outside the current window.

        Removes all entries older than (current_time - window_seconds).
        This keeps the log containing only requests within the sliding window.
        """
        current_time = time.time()
        window_start = current_time - self.window_seconds

        # Remove old entries from the front of the deque
        while self.log and self.log[0] < window_start:
            self.log.popleft()

    def allow_request(self) -> bool:
        """
        Check if a request should be allowed.

        This method:
        1. Removes timestamps outside the current window
        2. Counts remaining requests in the window
        3. If count < max_requests, ALLOW and record timestamp
        4. If count >= max_requests, REJECT

        Returns:
            True if the request is allowed, False if rejected.

        Example:
            limiter = SlidingWindowLog(max_requests=3, window_seconds=1)
            limiter.allow_request()  # True (log: [t1])
            limiter.allow_request()  # True (log: [t1, t2])
            limiter.allow_request()  # True (log: [t1, t2, t3])
            limiter.allow_request()  # False (3 requests in window)
        """
        with self._lock:
            self._cleanup_old_entries()

            if len(self.log) < self.max_requests:
                self.log.append(time.time())
                return True
            return False

    def get_request_count(self) -> int:
        """
        Get the number of requests in the current window (for debugging/demo).

        Returns:
            Number of requests in the sliding window.
        """
        with self._lock:
            self._cleanup_old_entries()
            return len(self.log)

    def get_oldest_timestamp(self) -> float:
        """
        Get the oldest timestamp in the log (for debugging/demo).

        Returns:
            The oldest timestamp, or None if log is empty.
        """
        with self._lock:
            self._cleanup_old_entries()
            if self.log:
                return self.log[0]
            return None

    def get_window_info(self) -> dict:
        """
        Get detailed window information (for debugging/demo).

        Returns:
            Dictionary with window statistics.
        """
        with self._lock:
            self._cleanup_old_entries()
            return {
                "request_count": len(self.log),
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds,
                "remaining": max(0, self.max_requests - len(self.log)),
            }
