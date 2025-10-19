# Monitoring Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User / Browser                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├─ http://localhost:3001 ──► Grafana Dashboard
                 ├─ http://localhost:9090 ──► Prometheus UI
                 └─ http://localhost:8000 ──► Django Application
                                               │
┌────────────────────────────────────────────┴────────────────────┐
│                    Monitoring Stack                             │
│                                                                  │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │   Grafana    │◄────────│  Prometheus  │                     │
│  │   :3001      │  Query  │    :9090     │                     │
│  │              │         │              │                     │
│  │ • Dashboards │         │ • Metrics DB │                     │
│  │ • Alerts     │         │ • Scraping   │                     │
│  │ • Users      │         │ • Alerts     │                     │
│  └──────────────┘         └───────┬──────┘                     │
│                                    │                             │
│                           ┌────────┴──────────┐                │
│                           │   Scrape Targets   │                │
│                           │   (every 15s)      │                │
│                           └────────┬───────────┘                │
│                                    │                             │
└────────────────────────────────────┼─────────────────────────────┘
                                     │
                 ┌───────────────────┼────────────────┐
                 │                   │                 │
    ┌────────────▼──────┐  ┌────────▼────────┐  ┌───▼──────────┐
    │  Django App       │  │  Redis          │  │  PostgreSQL  │
    │  :8000            │  │  Exporter       │  │  Exporter    │
    │                   │  │  :9121          │  │  :9187       │
    │ /api/v1/metrics   │  │                 │  │              │
    │                   │  │ Exposes:        │  │ Exposes:     │
    │ Middleware:       │  │ • Memory        │  │ • Queries    │
    │ • HTTP Metrics    │  │ • Commands      │  │ • Locks      │
    │ • DB Metrics      │  │ • Connections   │  │ • Cache      │
    │ • Custom Metrics  │  │ • Keyspace      │  │ • Size       │
    └───────────────────┘  └─────────────────┘  └──────────────┘
                                     │
                           ┌─────────▼────────┐
                           │  Celery Worker   │
                           │  :9808           │
                           │                  │
                           │ Exporter:        │
                           │ • Task counts    │
                           │ • Queue length   │
                           │ • Task duration  │
                           └──────────────────┘
```

## Data Flow

### 1. Metrics Collection

```
Application Code
      │
      ├─► HTTP Request ──► Middleware ──► Increment Counters
      ├─► DB Query ────► Middleware ──► Record Duration
      ├─► Cache Hit ───► Code ──────► Update Gauge
      └─► Custom Event ► Code ──────► Custom Metric
                                            │
                                            ▼
                                    Prometheus Client
                                   (In-Memory Registry)
                                            │
                          ┌─────────────────┴──────────────┐
                          │   Expose at /api/v1/metrics    │
                          │   Format: Prometheus Text      │
                          └────────────────┬───────────────┘
                                           │
                          ┌────────────────▼────────────────┐
                          │   Prometheus Scrapes            │
                          │   Every 15 seconds              │
                          └────────────────┬────────────────┘
                                           │
                          ┌────────────────▼────────────────┐
                          │   Store in TSDB                 │
                          │   Retention: 30 days            │
                          └─────────────────────────────────┘
```

### 2. Alerting Flow

```
Prometheus
    │
    ├─► Evaluate Alert Rules (every 15s)
    │        │
    │        ├─► Condition Met? ─NO─► Continue
    │        │
    │        └─► YES ─► Firing State
    │                      │
    │                      ├─► Show in Prometheus UI
    │                      ├─► Show in Grafana
    │                      └─► (Optional) Alertmanager
    │                                     │
    │                                     └─► Notifications
    │                                          (Slack, Email, etc.)
    └─────────────────────────────────────────────────────
```

### 3. Dashboard Visualization

```
User Opens Grafana Dashboard
         │
         ▼
Grafana Executes PromQL Queries
         │
         ▼
Query Prometheus API
         │
         ▼
Prometheus Returns Time Series Data
         │
         ▼
Grafana Renders:
  • Graphs (Time Series)
  • Gauges (Current Values)
  • Tables (Aggregations)
  • Alerts (Current State)
```

## Component Interactions

### HTTP Request Journey

```
1. User Request
   │
   ▼
2. Nginx/Load Balancer (if in production)
   │
   ▼
3. Django Application (:8000)
   │
   ├─► PrometheusMetricsMiddleware
   │    │
   │    ├─► Start Timer
   │    ├─► Increment request counter
   │    └─► Track request size
   │
   ├─► Application Logic
   │    │
   │    ├─► Database Queries
   │    │    └─► DatabaseMetricsMiddleware tracks
   │    │
   │    ├─► Cache Operations
   │    │    └─► Manual metrics in code
   │    │
   │    └─► Custom Business Logic
   │         └─► Custom metrics in code
   │
   └─► PrometheusMetricsMiddleware (Response)
        │
        ├─► Stop Timer
        ├─► Record duration
        ├─► Track response size
        └─► Increment status counter
```

### Celery Task Journey

```
1. Task Triggered
   │
   ▼
2. Sent to Redis Queue
   │
   ▼
3. Celery Worker Picks Up Task
   │
   ├─► Celery Exporter Tracks:
   │    │
   │    ├─► Task received
   │    ├─► Queue length
   │    └─► Worker state
   │
   ├─► Task Executes
   │    │
   │    └─► Custom metrics in task code
   │
   └─► Task Completes
        │
        └─► Celery Exporter Records:
             ├─► Task state (success/failure)
             ├─► Task duration
             └─► Queue length update
```

## Network Ports

| Service            | Port  | Purpose                    |
|--------------------|-------|----------------------------|
| Django App         | 8000  | Application + Metrics      |
| Prometheus         | 9090  | Metrics DB + UI            |
| Grafana            | 3001  | Dashboards + Visualization |
| Redis Exporter     | 9121  | Redis metrics              |
| PostgreSQL Export  | 9187  | Database metrics           |
| Celery Exporter    | 9808  | Celery task metrics        |
| Redis              | 6379  | Cache + Celery broker      |
| PostgreSQL         | 5432  | Database (internal)        |

## Metric Types & Storage

### Counter (Monotonic Increase)

```
django_http_requests_total{method="GET", endpoint="/api/v1/usr/"}
                 ▲
                 │
    ┌────────────┴─────────────┐
    │  Increments only         │
    │  Never decreases         │
    │  Use rate() for rate/s   │
    └──────────────────────────┘
```

### Histogram (Distribution)

```
django_http_request_duration_seconds
                 │
                 ├─► _bucket{le="0.1"}  = 50
                 ├─► _bucket{le="0.5"}  = 95
                 ├─► _bucket{le="1.0"}  = 99
                 ├─► _bucket{le="+Inf"} = 100
                 ├─► _sum = 42.5
                 └─► _count = 100

Use histogram_quantile() for percentiles
```

### Gauge (Can Increase/Decrease)

```
django_db_connections_active
                 ▲
                 │
    ┌────────────┴─────────────┐
    │  Current value           │
    │  Goes up and down        │
    │  No rate() needed        │
    └──────────────────────────┘
```

## Scaling Considerations

### Current Setup (Single Instance)

```
┌─────────────┐
│ Prometheus  │ ◄─ Scrapes all targets
└─────────────┘
       │
       ▼
  Local TSDB (30 days)
```

### Production Setup (HA)

```
┌─────────────┐      ┌─────────────┐
│ Prometheus  │      │ Prometheus  │
│  Instance 1 │      │  Instance 2 │
└──────┬──────┘      └──────┬──────┘
       │                     │
       └──────────┬──────────┘
                  ▼
         ┌────────────────┐
         │  Remote Write  │
         │   (Thanos/     │
         │    Cortex)     │
         └────────────────┘
                  │
                  ▼
         Long-term Storage
```

## Security Layers

```
┌────────────────────────────────────────────┐
│  Network Layer                             │
│  • Docker network isolation                │
│  • Port restrictions                       │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│  Application Layer                         │
│  • Middleware authentication (optional)    │
│  • Metrics endpoint on app port            │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│  Grafana Layer                             │
│  • User authentication                     │
│  • RBAC (optional)                         │
│  • HTTPS (production)                      │
└────────────────────────────────────────────┘
```

## Monitoring the Monitors

```
Prometheus monitors itself:
├─► Scrape duration
├─► Rule evaluation time
├─► TSDB size
└─► Target health

Grafana:
├─► API health endpoint
├─► Login metrics
└─► Dashboard load time
```

---

**This architecture provides:**
- ✅ Comprehensive observability
- ✅ Scalable design
- ✅ Minimal performance impact
- ✅ Production-ready setup

