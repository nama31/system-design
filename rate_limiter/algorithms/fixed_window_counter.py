"""
Fixed Window Counter Algorithm

This module implements the Fixed Window Counter rate limiting algorithm.
"""

import time
import threading


class FixedWindowCounter:
    """
    Fixed Window Counter Rate Limiter

    HOW IT WORKS:
    -------------
    Time is divided into fixed-size windows (e.g., 1 second, 1 minute).
    Each window has a counter that tracks the number of requests. When a
    request arrives:

    - If we're in a new window, reset the counter to 0
    - If the counter is below the limit, ALLOW the request and increment
    - If the counter is at or above the limit, REJECT the request

    VISUAL REPRESENTATION:
    ----------------------
        Time:     |----1s----|----1s----|----1s----|
        Window:   [  Window  ][  Window  ][  Window ]
        Counter:  [    5     ][    3     ][    0    ]
        Limit:    [   10     ][   10     ][   10    ]
                      OK         OK        OK

        Time:     |----1s----|
        Window:   [  Window  ]
        Counter:  [   10     ]  ← At limit!
        Limit:    [   10     ]
                     REJECT

    ADVANTAGES:
    -----------
    - Very simple to implement
    - Memory efficient (only stores counter + window start)
    - Fast O(1) operations
    - Easy to reason about

    DISADVANTAGES:
    --------------
    - Boundary problem: Can allow 2x burst at window boundaries
      (e.g., 10 requests at end of window 1 + 10 at start of window 2)
    - Sudden spike at window reset
    - Not smooth rate limiting

    TYPICAL USE CASES:
    ------------------
    - Simple API rate limiting
    - Counting events per time period
    - Analytics and metrics collection
    - When exact rate limiting isn't critical
    """

    def __init__(self, max_requests: int, window_seconds: float):
        """
        Initialize the Fixed Window Counter.

        Args:
            max_requests: Maximum number of requests allowed per window.
            window_seconds: Duration of each time window in seconds.

        Example:
            # Allow 100 requests per minute
            limiter = FixedWindowCounter(max_requests=100, window_seconds=60)

            # Allow 10 requests per second
            limiter = FixedWindowCounter(max_requests=10, window_seconds=1)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.counter = 0
        self.window_start = time.time()
        self._lock = threading.Lock()

    def _reset_if_new_window(self):
        """
        Reset the counter if we've entered a new time window.

        Checks if the current time has moved past the current window.
        If so, starts a new window with counter reset to 0.
        """
        current_time = time.time()

        # Check if we've moved to a new window
        if current_time - self.window_start >= self.window_seconds:
            # Calculate the start of the new window
            # This aligns windows to consistent boundaries
            elapsed_windows = int((current_time - self.window_start) / self.window_seconds)
            self.window_start += elapsed_windows * self.window_seconds
            self.counter = 0

    def allow_request(self) -> bool:
        """
        Check if a request should be allowed.

        This method:
        1. Checks if we're in a new window (resets if needed)
        2. If counter < max_requests, ALLOW and increment counter
        3. If counter >= max_requests, REJECT

        Returns:
            True if the request is allowed, False if rejected.

        Example:
            limiter = FixedWindowCounter(max_requests=3, window_seconds=1)
            limiter.allow_request()  # True (counter: 1)
            limiter.allow_request()  # True (counter: 2)
            limiter.allow_request()  # True (counter: 3)
            limiter.allow_request()  # False (at limit!)
        """
        with self._lock:
            self._reset_if_new_window()

            if self.counter < self.max_requests:
                self.counter += 1
                return True
            return False

    def get_counter(self) -> int:
        """
        Get the current request count in this window (for debugging/demo).

        Returns:
            Current counter value.
        """
        with self._lock:
            self._reset_if_new_window()
            return self.counter

    def get_remaining(self) -> int:
        """
        Get the number of remaining requests allowed in this window.

        Returns:
            Number of requests still allowed before hitting the limit.
        """
        with self._lock:
            self._reset_if_new_window()
            return max(0, self.max_requests - self.counter)
