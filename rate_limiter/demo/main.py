"""
Rate Limiter Demo

This module demonstrates all rate limiting algorithms with example usage.
Run this file to see each algorithm in action.
"""

import time
import sys
import os

# Add project root to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rate_limiter.algorithms.token_bucket import TokenBucket
from rate_limiter.algorithms.leaky_bucket import LeakyBucket
from rate_limiter.algorithms.fixed_window_counter import FixedWindowCounter
from rate_limiter.algorithms.sliding_window_log import SlidingWindowLog
from rate_limiter.algorithms.sliding_window_counter import SlidingWindowCounter


def print_separator(title: str):
    """Print a formatted section separator."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demo_token_bucket():
    """
    Demonstrate the Token Bucket algorithm.

    Shows how tokens are consumed and how the bucket refills over time.
    """
    print_separator("Token Bucket Algorithm")
    print("Configuration: max_tokens=5, refill_rate=2 tokens/second")
    print("This allows bursts of up to 5 requests, then 2/second sustained.\n")

    # Create bucket: 5 tokens max, refills at 2 tokens/second
    bucket = TokenBucket(max_tokens=5, refill_rate=2)

    print("Sending 8 rapid requests (should allow 5, reject 3):")
    for i in range(1, 9):
        result = bucket.allow_request()
        status = "Allowed" if result else "Rejected"
        tokens = bucket.get_tokens()
        print(f"  Request {i} -> {status:8} (tokens remaining: {tokens:.1f})")

    print("\nWaiting 1 second for refill...")
    time.sleep(1)

    print(f"\nAfter 1 second: {bucket.get_tokens():.1f} tokens available")
    print("Sending 3 more requests:")
    for i in range(1, 4):
        result = bucket.allow_request()
        status = "Allowed" if result else "Rejected"
        print(f"  Request {i} -> {status}")


def demo_leaky_bucket():
    """
    Demonstrate the Leaky Bucket algorithm.

    Shows how requests queue up and are processed at a constant rate.
    """
    print_separator("Leaky Bucket Algorithm")
    print("Configuration: capacity=4, leak_rate=2 requests/second")
    print("Requests queue up and drain at a steady 2/second rate.\n")

    # Create bucket: holds 4 requests, leaks at 2/second
    bucket = LeakyBucket(capacity=4, leak_rate=2)

    print("Sending 6 rapid requests (queue fills, then overflows):")
    for i in range(1, 7):
        result = bucket.allow_request()
        status = "Allowed" if result else "Rejected"
        queue_size = bucket.get_queue_size()
        print(f"  Request {i} -> {status:8} (queue size: {queue_size})")

    print("\nWaiting 1.5 seconds for requests to leak...")
    time.sleep(1.5)

    print(f"\nAfter 1.5 seconds: queue size = {bucket.get_queue_size()}")
    print("Sending 2 more requests:")
    for i in range(1, 3):
        result = bucket.allow_request()
        status = "Allowed" if result else "Rejected"
        print(f"  Request {i} -> {status}")


def demo_fixed_window_counter():
    """
    Demonstrate the Fixed Window Counter algorithm.

    Shows how requests are counted within fixed time windows.
    """
    print_separator("Fixed Window Counter Algorithm")
    print("Configuration: max_requests=5, window=2 seconds")
    print("Each 2-second window allows exactly 5 requests.\n")

    limiter = FixedWindowCounter(max_requests=5, window_seconds=2)

    print("Sending 7 rapid requests (5 allowed, 2 rejected):")
    for i in range(1, 8):
        result = limiter.allow_request()
        status = "Allowed" if result else "Rejected"
        remaining = limiter.get_remaining()
        print(f"  Request {i} -> {status:8} (remaining in window: {remaining})")

    print("\nWaiting 2.5 seconds for new window...")
    time.sleep(2.5)

    print(f"\nNew window started: {limiter.get_remaining()} requests remaining")
    print("Sending 3 more requests:")
    for i in range(1, 4):
        result = limiter.allow_request()
        status = "Allowed" if result else "Rejected"
        print(f"  Request {i} -> {status}")


def demo_sliding_window_log():
    """
    Demonstrate the Sliding Window Log algorithm.

    Shows precise rate limiting using timestamp logs.
    """
    print_separator("Sliding Window Log Algorithm")
    print("Configuration: max_requests=5, window=2 seconds")
    print("Tracks exact timestamps for precise rate limiting.\n")

    limiter = SlidingWindowLog(max_requests=5, window_seconds=2)

    print("Sending 7 rapid requests (5 allowed, 2 rejected):")
    for i in range(1, 8):
        result = limiter.allow_request()
        status = "Allowed" if result else "Rejected"
        count = limiter.get_request_count()
        print(f"  Request {i} -> {status:8} (requests in window: {count})")

    print("\nWaiting 2.5 seconds for old requests to expire...")
    time.sleep(2.5)

    info = limiter.get_window_info()
    print(f"\nAfter wait: {info['request_count']} requests in window")
    print("Sending 3 more requests:")
    for i in range(1, 4):
        result = limiter.allow_request()
        status = "Allowed" if result else "Rejected"
        print(f"  Request {i} -> {status}")


def demo_sliding_window_counter():
    """
    Demonstrate the Sliding Window Counter algorithm.

    Shows the hybrid approach with weighted counters.
    """
    print_separator("Sliding Window Counter Algorithm")
    print("Configuration: max_requests=5, window=2 seconds")
    print("Uses weighted counters from current + previous windows.\n")

    limiter = SlidingWindowCounter(max_requests=5, window_seconds=2)

    print("Sending 7 rapid requests (approximately 5 allowed):")
    for i in range(1, 8):
        result = limiter.allow_request()
        status = "Allowed" if result else "Rejected"
        info = limiter.get_window_info()
        print(f"  Request {i} -> {status:8} (weighted count: {info['weighted_count']:.1f})")

    print("\nWaiting 1 second (half window)...")
    time.sleep(1)

    info = limiter.get_window_info()
    print(f"\nAfter 1 second:")
    print(f"  Previous window count: {info['previous_count']}")
    print(f"  Current window count: {info['current_count']}")
    print(f"  Weighted count: {info['weighted_count']:.1f}")

    print("\nSending 3 more requests:")
    for i in range(1, 4):
        result = limiter.allow_request()
        status = "Allowed" if result else "Rejected"
        info = limiter.get_window_info()
        print(f"  Request {i} -> {status:8} (weighted count: {info['weighted_count']:.1f})")


def comparison_demo():
    """
    Compare all algorithms side by side.

    Shows how each algorithm handles the same request pattern.
    """
    print_separator("Algorithm Comparison")
    print("All algorithms configured for ~5 requests per 2 seconds")
    print("Sending 10 rapid requests to each algorithm:\n")

    # Configure all algorithms with similar limits
    algorithms = {
        "Token Bucket": TokenBucket(max_tokens=5, refill_rate=2.5),
        "Leaky Bucket": LeakyBucket(capacity=5, leak_rate=2.5),
        "Fixed Window": FixedWindowCounter(max_requests=5, window_seconds=2),
        "Sliding Log": SlidingWindowLog(max_requests=5, window_seconds=2),
        "Sliding Counter": SlidingWindowCounter(max_requests=5, window_seconds=2),
    }

    # Track results for each algorithm
    results = {name: {"allowed": 0, "rejected": 0} for name in algorithms}

    # Send 10 requests to each algorithm
    for name, algo in algorithms.items():
        for _ in range(10):
            if algo.allow_request():
                results[name]["allowed"] += 1
            else:
                results[name]["rejected"] += 1

    # Print comparison table
    print(f"{'Algorithm':<20} {'Allowed':>10} {'Rejected':>10}")
    print("-" * 42)
    for name, stats in results.items():
        print(f"{name:<20} {stats['allowed']:>10} {stats['rejected']:>10}")

    print("\nNote: Results vary based on algorithm characteristics:")
    print("  - Token Bucket: Allows burst up to max_tokens")
    print("  - Leaky Bucket: Queues requests, smooth output")
    print("  - Fixed Window: Strict per-window limit")
    print("  - Sliding Log: Precise sliding window")
    print("  - Sliding Counter: Approximate sliding window")


def main():
    """Run all demonstrations."""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "     RATE LIMITING ALGORITHMS - EDUCATIONAL DEMO     ".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)

    demo_token_bucket()
    demo_leaky_bucket()
    demo_fixed_window_counter()
    demo_sliding_window_log()
    demo_sliding_window_counter()
    comparison_demo()

    print("\n" + "=" * 60)
    print(" Demo Complete!")
    print("=" * 60)
    print("\nSee RateLimitingNotes.md for detailed explanations of")
    print("each algorithm's advantages, disadvantages, and use cases.")
    print()


if __name__ == "__main__":
    main()
