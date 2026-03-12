"""
Leaky Bucket Algorithm

This module implements the Leaky Bucket rate limiting algorithm.
"""

import time
import threading
from collections import deque


class LeakyBucket:
    """
    Leaky Bucket Rate Limiter

    HOW IT WORKS:
    -------------
    Imagine a bucket with a hole at the bottom. Water (requests) flows into
    the bucket at variable rates, but leaks out at a constant rate. If the
    bucket overflows, excess water is lost (requests are rejected).

    - Requests are added to a queue (the bucket)
    - Requests are processed at a constant rate (the leak)
    - If the bucket is full, new requests are REJECTED
    - If the bucket has space, requests are ALLOWED and queued

    VISUAL REPRESENTATION:
    ----------------------
        Requests in
            ↓
        ┌─────────────┐
        │  BUCKET     │  ← Queue of pending requests
        │  ~~~~~~~    │  ← Water level (queue size)
        │     ↓       │  ← Leaks at constant rate
        └─────────────┘
            ↓
        Processed at steady rate

    ADVANTAGES:
    -----------
    - Enforces a strict, constant output rate
    - Smooths out bursty traffic
    - Prevents downstream system overload
    - Simple FIFO processing order

    DISADVANTAGES:
    --------------
    - No burst allowance (unlike Token Bucket)
    - Can introduce latency (requests wait in queue)
    - May reject requests even when average rate is low
    - Requires queue management

    TYPICAL USE CASES:
    ------------------
    - Database connection pooling
    - Message queue rate limiting
    - Video streaming: constant bitrate enforcement
    - Print spooling
    - Any system requiring steady, predictable throughput
    """

    def __init__(self, capacity: int, leak_rate: float):
        """
        Initialize the Leaky Bucket.

        Args:
            capacity: Maximum number of requests the bucket can hold.
                     This is the queue size limit.
            leak_rate: Number of requests processed per second.
                      Controls the constant output rate.

        Example:
            # Process 5 requests per second, max queue of 10
            bucket = LeakyBucket(capacity=10, leak_rate=5)
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.queue = deque()  # Holds timestamps of queued requests
        self._lock = threading.Lock()

    def _leak(self):
        """
        Remove processed requests from the queue.

        Calculates how many requests should have been processed (leaked)
        based on elapsed time and removes them from the front of the queue.
        """
        if not self.queue:
            return

        current_time = time.time()

        # Calculate how many requests should have leaked
        # Time difference * leak rate = number of leaked requests
        while self.queue:
            oldest_request = self.queue[0]
            time_in_bucket = current_time - oldest_request

            # If enough time has passed for this request to leak out
            if time_in_bucket >= 1.0 / self.leak_rate:
                self.queue.popleft()
            else:
                break

    def allow_request(self) -> bool:
        """
        Check if a request should be allowed.

        This method:
        1. Leaks (processes) old requests from the queue
        2. Checks if there's space in the bucket
        3. If yes, adds the request to the queue and returns True
        4. If no (bucket full), returns False (request rejected)

        Returns:
            True if the request is allowed (added to queue),
            False if rejected (bucket full).

        Example:
            bucket = LeakyBucket(capacity=3, leak_rate=1)
            bucket.allow_request()  # True (queue: [t1])
            bucket.allow_request()  # True (queue: [t1, t2])
            bucket.allow_request()  # True (queue: [t1, t2, t3])
            bucket.allow_request()  # False (bucket full!)
        """
        with self._lock:
            self._leak()

            if len(self.queue) < self.capacity:
                self.queue.append(time.time())
                return True
            return False

    def get_queue_size(self) -> int:
        """
        Get the current queue size (for debugging/demo).

        Returns:
            Number of requests currently in the bucket.
        """
        with self._lock:
            self._leak()
            return len(self.queue)

    def get_wait_time(self) -> float:
        """
        Estimate how long a new request would wait before processing.

        Returns:
            Estimated wait time in seconds, or 0 if queue is empty.
        """
        with self._lock:
            self._leak()
            if not self.queue:
                return 0.0
            # Each request in queue adds 1/leak_rate seconds of wait
            return len(self.queue) / self.leak_rate
