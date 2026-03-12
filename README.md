# Rate Limiting Algorithms - Learning Notes

This document provides educational notes on the five rate limiting algorithms implemented in this project.

---

## Table of Contents

1. [Token Bucket](#1-token-bucket)
2. [Leaky Bucket](#2-leaky-bucket)
3. [Fixed Window Counter](#3-fixed-window-counter)
4. [Sliding Window Log](#4-sliding-window-log)
5. [Sliding Window Counter](#5-sliding-window-counter)
6. [Comparison Summary](#6-comparison-summary)

---

## 1. Token Bucket

### Concept

The Token Bucket algorithm uses a metaphor of a bucket that holds tokens:

- **Bucket capacity**: Maximum number of tokens (max_tokens)
- **Refill rate**: Tokens added per second (refill_rate)
- **Request handling**: Each request consumes one token

```
        Tokens added at refill_rate
              ↓
    ┌─────────────────┐
    │    BUCKET       │  Capacity: max_tokens
    │   [●●●○○]       │  Current: 3 tokens
    └─────────────────┘
              ↓
        Request takes 1 token
```

**How it works:**
1. Tokens accumulate in the bucket at the refill rate
2. Bucket cannot exceed max_tokens (excess tokens are discarded)
3. When a request arrives:
   - If tokens ≥ 1: consume one token, allow request
   - If tokens < 1: reject request

### Advantages

| Advantage | Explanation |
|-----------|-------------|
| **Burst allowance** | Can handle sudden spikes up to max_tokens |
| **Flexible** | Allows idle periods to build up tokens |
| **Simple** | Easy to understand and implement |
| **Smooth limiting** | Provides consistent rate over time |

### Disadvantages

| Disadvantage | Explanation |
|--------------|-------------|
| **Burst risk** | Large bursts may overwhelm downstream systems |
| **State tracking** | Must track token count and last refill time |
| **Not strict** | Less predictable than Leaky Bucket |

### Real-World Use Cases

- **API Rate Limiting**: GitHub API, Twitter API allow burst usage
- **Cloud Services**: AWS rate limits with burst capacity
- **Gaming**: Ability cooldowns with stored charges
- **Network Traffic**: Traffic shaping with burst tolerance

---

## 2. Leaky Bucket

### Concept

The Leaky Bucket algorithm uses a metaphor of a bucket with a hole:

- **Bucket capacity**: Maximum queue size
- **Leak rate**: Requests processed per second
- **Request handling**: Requests queue up and drain at constant rate

```
    Requests in (variable rate)
          ↓
    ┌─────────────┐
    │   BUCKET    │  Queue: [req1, req2, req3]
    │   ~~~~~~    │  Water level = queue size
    │      ↓      │  Leaks at constant rate
    └─────────────┘
          ↓
    Processed (steady rate)
```

**How it works:**
1. Requests enter the bucket (queue)
2. Requests are processed at a constant leak rate
3. If bucket is full, new requests are rejected
4. If bucket has space, requests are queued

### Advantages

| Advantage | Explanation |
|-----------|-------------|
| **Constant output** | Enforces strict, predictable rate |
| **Smooths bursts** | Converts bursty input to steady output |
| **Protects downstream** | Prevents system overload |
| **FIFO order** | Requests processed in order |

### Disadvantages

| Disadvantage | Explanation |
|--------------|-------------|
| **No burst** | Cannot handle sudden spikes |
| **Latency** | Requests may wait in queue |
| **Queue management** | Requires maintaining request queue |
| **Strict rejection** | May reject during temporary spikes |

### Real-World Use Cases

- **Database Connections**: Connection pool rate limiting
- **Message Queues**: Kafka, RabbitMQ throughput control
- **Video Streaming**: Constant bitrate enforcement
- **Print Spooling**: Managing print job flow
- **Payment Processing**: Steady transaction processing

---

## 3. Fixed Window Counter

### Concept

The Fixed Window Counter divides time into fixed windows and counts requests per window:

- **Window size**: Duration of each time window
- **Max requests**: Limit per window
- **Request handling**: Count requests, reset at window boundary

```
Time:   |----1s----|----1s----|----1s----|
Window: [ Window 1 ][ Window 2 ][ Window 3 ]
Count:  [    5     ][    3     ][    0     ]
Limit:  [   10     ][   10     ][   10     ]
Status: [   OK     ][   OK     ][   OK     ]
```

**How it works:**
1. Track current window start time and request count
2. When a request arrives:
   - If new window: reset counter, update window start
   - If count < max: increment counter, allow request
   - If count >= max: reject request

### Advantages

| Advantage | Explanation |
|-----------|-------------|
| **Simple** | Easiest to implement |
| **Memory efficient** | Only stores counter + timestamp |
| **Fast** | O(1) operations |
| **Predictable** | Clear window boundaries |

### Disadvantages

| Disadvantage | Explanation |
|--------------|-------------|
| **Boundary problem** | Can allow 2x burst at window edges |
| **Sudden resets** | Counter resets cause rate spikes |
| **Not smooth** | Jerky rate limiting at boundaries |

**Boundary Problem Example:**
```
Window 1 ends at t=1.0s, Window 2 starts at t=1.0s

t=0.9s: 10 requests (Window 1, at limit)
t=1.0s: Window resets
t=1.0s: 10 more requests (Window 2, fresh limit)

Result: 20 requests in 0.1 seconds!
```

### Real-World Use Cases

- **Simple API Limits**: Basic rate limiting for small APIs
- **Analytics**: Counting events per time period
- **Metrics Collection**: Prometheus-style counters
- **When precision isn't critical**: Internal services

---

## 4. Sliding Window Log

### Concept

The Sliding Window Log maintains a log of timestamps for all requests in the window:

- **Window size**: Duration of sliding window
- **Max requests**: Limit within any sliding window
- **Request handling**: Store timestamps, remove old ones

```
Time: ----|----|----|----|----|---->
          t-3  t-2  t-1   t   t+1

Log at time t: [t-2.5, t-1.8, t-0.5]
                 ↑_______________↑
                 Window: [t-3, t]

As time slides, old entries fall out
```

**How it works:**
1. Maintain a log (deque) of request timestamps
2. When a request arrives:
   - Remove timestamps older than (now - window_size)
   - If log size < max: add timestamp, allow request
   - If log size >= max: reject request

### Advantages

| Advantage | Explanation |
|-----------|-------------|
| **Precise** | Exact rate limiting, no boundary issues |
| **Smooth** | No sudden spikes or resets |
| **Accurate** | True sliding window behavior |
| **Fair** | Consistent limiting at all times |

### Disadvantages

| Disadvantage | Explanation |
|--------------|-------------|
| **Memory intensive** | Stores timestamp per request |
| **Slower cleanup** | O(n) to remove old entries |
| **Not scalable** | Poor for high-throughput systems |
| **Storage overhead** | Can grow large with many requests |

### Real-World Use Cases

- **Login Rate Limiting**: Security-critical applications
- **Low-volume APIs**: Precise limiting for expensive operations
- **Audit Systems**: When request history is needed anyway
- **Anti-abuse**: CAPTCHA triggering, fraud detection

---

## 5. Sliding Window Counter

### Concept

The Sliding Window Counter is a hybrid approach using weighted counters:

- **Window size**: Duration of each fixed window
- **Max requests**: Limit per sliding window
- **Request handling**: Weighted average of current + previous window

```
Time:     |----1s----|----1s----|
Window:   [ Previous ][ Current ]
Count:    [    8     ][    4     ]

At t = 0.5s into current window:
- 50% of previous window still in sliding window
- Weighted count = (8 × 0.5) + 4 = 8 requests

Sliding window: [----prev 50%----|----curr 50%----]
```

**How it works:**
1. Track counters for current and previous windows
2. When a request arrives:
   - Update windows if needed (shift current→previous)
   - Calculate weighted count: `(prev × weight) + current`
   - Weight = portion of previous window in sliding window
   - If weighted < max: increment current, allow request
   - Otherwise: reject request

### Advantages

| Advantage | Explanation |
|-----------|-------------|
| **No boundary problem** | Smooths across window edges |
| **Memory efficient** | Only 2 counters needed |
| **Good approximation** | Close to true sliding window |
| **Fast** | O(1) operations |
| **Scalable** | Works well in distributed systems |

### Disadvantages

| Disadvantage | Explanation |
|--------------|-------------|
| **Approximation** | Not exact (slight over/under counting) |
| **More complex** | Harder to understand than Fixed Window |
| **Some boundary effects** | Reduced but not eliminated |

### Real-World Use Cases

- **High-throughput APIs**: Google, Netflix rate limiting
- **Distributed Systems**: Easy to aggregate across nodes
- **Redis-based Limiting**: INCR with expiration
- **Cloud Load Balancers**: AWS ALB, CloudFlare
- **Microservices**: Service mesh rate limiting

---

## 6. Comparison Summary

### Algorithm Comparison Table

| Algorithm | Memory | Speed | Burst | Precision | Best For |
|-----------|--------|-------|-------|-----------|----------|
| Token Bucket | O(1) | O(1) | ✅ Yes | Medium | APIs with burst allowance |
| Leaky Bucket | O(n)* | O(1) | ❌ No | High | Steady throughput systems |
| Fixed Window | O(1) | O(1) | ⚠️ Edge | Low | Simple implementations |
| Sliding Log | O(n) | O(n) | ❌ No | ✅ Exact | Security, low-volume |
| Sliding Counter | O(1) | O(1) | ❌ No | High | High-throughput APIs |

*Leaky Bucket queue size depends on capacity

### When to Use Each Algorithm

```
┌─────────────────────────────────────────────────────────────┐
│  Need burst allowance?                                      │
│  ├── Yes → Token Bucket                                     │
│  └── No → Continue...                                       │
│                                                             │
│  Need steady output rate?                                   │
│  ├── Yes → Leaky Bucket                                     │
│  └── No → Continue...                                       │
│                                                             │
│  High throughput system?                                    │
│  ├── Yes → Sliding Window Counter                           │
│  └── No → Continue...                                       │
│                                                             │
│  Need exact precision?                                      │
│  ├── Yes → Sliding Window Log                               │
│  └── No → Fixed Window Counter (simplest)                   │
└─────────────────────────────────────────────────────────────┘
```

### Key Takeaways

1. **Token Bucket**: Best for user-facing APIs where occasional bursts are acceptable
2. **Leaky Bucket**: Best for protecting downstream systems with steady processing
3. **Fixed Window**: Good for simple use cases where precision isn't critical
4. **Sliding Log**: Best for security-critical applications requiring exact limits
5. **Sliding Counter**: Best for high-scale distributed systems

---

## Running the Demo

```bash
# From the project root directory
python -m rate_limiter.demo.main
```

Or directly:

```bash
python rate_limiter/demo/main.py
```

---

## Further Reading

- **Rate Limiting at Scale**: Netflix Tech Blog
- **API Rate Limiting**: Stripe Engineering
- **Distributed Rate Limiting**: Redis + Lua scripts
- **Envoy Proxy**: Rate limiting filters
- **Kong Gateway**: Rate limiting plugins
