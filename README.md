# System Design: Scalable Notification System

## 1. Introduction
A scalable notification system is a critical component of modern applications, responsible for delivering millions (or billions) of messages across multiple channels—such as push notifications, SMS, and email—in real time. The system must be highly available, fault-tolerant, and capable of handling sudden spikes in traffic without degrading performance.

This document outlines the architecture, data models, core components, and best practices required to build an enterprise-grade notification system.

---

## 2. Requirements

### 2.1 Functional Requirements
* **Multi-Channel Support:** The system must send notifications via Push (iOS/Android), SMS, and Email.
* **Template Management:** Support for dynamic message templates (e.g., "Hello {name}, your order {order_id} is shipped").
* **User Preferences:** Users should be able to opt-in or opt-out of specific notification types and channels.
* **Prioritization:** Notifications should have priority levels (e.g., OTPs are high priority; promotional emails are low priority).
* **Scheduling:** Ability to schedule notifications for a future date/time.

### 2.2 Non-Functional Requirements
* **High Availability (HA):** The system must survive node or data center failures.
* **High Throughput & Low Latency:** Capable of processing thousands of requests per second with minimal delay for transactional messages.
* **Reliability:** At-least-once delivery guarantee. Notifications must not be lost.
* **Scalability:** Horizontal scaling to handle traffic bursts (e.g., breaking news, Black Friday sales).
* **Rate Limiting:** Prevent overwhelming the user (spam protection) and downstream third-party providers.

---

## 3. High-Level Architecture

The architecture follows a distributed, asynchronous, and event-driven model.

### 3.1 Step-by-Step Data Flow
1. **Trigger:** A client service (e.g., Billing Service, Order Service) sends a request to the Notification API Gateway.
2. **Validation & Metadata Retrieval:** The Notification Service validates the request, fetches the user's contact info (device tokens, email, phone) from the Database, and checks user preferences (has the user muted this category?).
3. **Queueing:** The service constructs the final message payload and pushes it into an appropriate Message Queue (e.g., Kafka or RabbitMQ) based on the channel and priority.
4. **Processing:** Dedicated workers (Push Worker, SMS Worker, Email Worker) pull messages from the queues.
5. **Dispatch:** The workers call the respective third-party APIs (APNs for iOS, FCM for Android, Twilio for SMS, SendGrid for Email).
6. **Tracking & Retry:** Success/Failure responses are logged. Failures due to transient errors are sent to a Retry Queue. Persistent failures go to a Dead Letter Queue (DLQ).

---

## 4. Core Components Deep Dive

### 4.1 API Gateway & Notification Servers
* **Stateless Design:** Notification servers should be completely stateless, allowing them to scale horizontally behind a load balancer.
* **Authentication & Rate Limiting:** The API gateway ensures that only authorized internal microservices can trigger notifications and applies tenant-level rate limiting.

### 4.2 Caching Layer (Redis / Memcached)
* **Device Tokens & Profiles:** Fetching user data from the DB for every notification is slow. Frequently accessed data (like device tokens and user preferences) is cached in Redis.
* **Deduplication:** A distributed cache is used to ensure the same notification is not sent multiple times within a short window. The system caches a hash of the `(user_id + message_id)` with a short TTL.

### 4.3 Database Storage
* **Relational Database (PostgreSQL / MySQL):** Used to store user profiles, device tokens, notification templates, and user preferences. These require ACID properties and complex joins.
* **NoSQL / Time-Series Database (Cassandra / MongoDB):** Used to store notification logs, delivery statuses, and analytics data. This data grows exponentially and requires high write throughput.

### 4.4 Message Queues (Apache Kafka / RabbitMQ)
Queues act as shock absorbers during traffic spikes, decoupling the message generation from the actual dispatch.
* **Channel Segregation:** Separate topics/queues for iOS, Android, SMS, and Email.
* **Priority Segregation:** Separate queues for High Priority (OTPs, Security Alerts) and Low Priority (Marketing).

### 4.5 Dispatch Workers
Microservices written in high-concurrency languages (like Go, Java, or Rust). They consume messages, apply third-party API keys, and manage HTTP connections to external providers.

---

## 5. Advanced System Design Concepts

### 5.1 Retry Mechanism and Dead-Letter Queues (DLQ)
Third-party services (APNs, Twilio) can experience downtime or rate-limit your requests.
* **Exponential Backoff:** If a message fails, the worker puts it into a delayed retry queue. The delay increases exponentially (e.g., 2s, 4s, 8s, 16s) to prevent hammering the failing third-party API.
* **DLQ:** If a message fails after maximum retries (e.g., 5 times), it is moved to a DLQ for manual inspection or alerting.

### 5.2 Rate Limiting and Throttling
* **Provider Limits:** Third-party APIs strictly rate-limit incoming requests. Workers must implement client-side throttling (e.g., using Token Bucket or Leaky Bucket algorithms) to avoid being temporarily banned.
* **User Fatigue:** A "Notification Frequency Cap" service checks how many promotional messages a user has received in the last 24 hours. If the limit is exceeded, the message is dropped.

### 5.3 At-Least-Once vs. Exactly-Once Delivery
Due to the nature of distributed systems and network partitions, achieving "exactly-once" delivery is incredibly difficult and expensive.
* The system is designed for **At-Least-Once delivery**.
* To mitigate duplicates, the deduplication cache (mentioned in 4.2) and idempotency keys are utilized.

### 5.4 Bulk Notifications & Batching
For sending a breaking news alert to 10 million users:
* A `BatchProcessor` service splits the massive user list into smaller chunks (e.g., 10,000 users per chunk).
* These chunks are distributed across multiple partitions in Kafka.
* Hundreds of workers process the partitions in parallel, reducing the total delivery time from hours to seconds.

---

## 6. Analytics, Tracking, and Observability

To ensure the system is healthy and to provide business metrics:
* **Delivery Status Callbacks:** Webhooks from SendGrid or Twilio are processed by a Feedback Service to update the status in the NoSQL database (e.g., Delivered, Bounced, Clicked).
* **Metrics & Monitoring:** Use Prometheus & Grafana to monitor Queue Depth (lag), Message Processing Rate, and Error Rates.
* **Alerting:** PagerDuty integration triggers alerts if queue lag exceeds a specific threshold or if third-party API failure rates spike.

---

## 7. Conclusion
Building a scalable notification system requires careful decoupling of components using message queues, robust retry mechanisms, and a dual-database approach for handling configurations vs. massive telemetry data. By implementing priority queues, strict rate limiting, and extensive monitoring, the system can reliably handle billions of messages across a diverse global user base.
