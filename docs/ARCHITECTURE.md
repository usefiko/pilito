# Pilito Architecture - Docker Swarm High Availability

## System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          DOCKER SWARM CLUSTER                               │
│                         High Availability Setup                             │
└────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   Load Balancer │
                              │  (Swarm Ingress)│
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
            ┌───────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
            │  Django Web  │   │ Django Web  │   │ Django Web  │
            │  Replica #1  │   │ Replica #2  │   │ Replica #3  │
            │  Container   │   │ Container   │   │ Container   │
            └───────┬──────┘   └──────┬──────┘   └──────┬──────┘
                    │                 │                  │
                    └─────────┬───────┴──────────────────┘
                              │
                   Overlay Network (10.0.10.0/24)
                              │
        ┌─────────────────────┼─────────────────────────────────┐
        │                     │                                  │
┌───────▼────────┐   ┌────────▼────────┐              ┌─────────▼──────────┐
│  PostgreSQL    │   │     Redis       │              │   Celery Workers   │
│  (pgvector)    │   │   Cache/Queue   │              │                    │
│  Replica: 1    │   │   Replica: 1    │              │ ┌────────────────┐ │
│                │   │                 │              │ │  Worker #1     │ │
│  Health: ✓     │   │  Health: ✓      │              │ └────────────────┘ │
│  Port: 5432    │   │  Port: 6379     │              │ ┌────────────────┐ │
└────────────────┘   └─────────────────┘              │ │  Worker #2     │ │
                                                       │ └────────────────┘ │
                                                       │                    │
                                                       │  Celery Beat: ✓    │
                                                       └────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                        MONITORING STACK                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐         ┌──────────────────┐                       │
│  │   Prometheus    │────────▶│     Grafana      │                       │
│  │  Port: 9090     │         │   Port: 3001     │                       │
│  │  Metrics Store  │         │   Dashboards     │                       │
│  └────────┬────────┘         └──────────────────┘                       │
│           │                                                               │
│           │ Scrapes metrics from:                                        │
│           ├─────────── Django (Django Metrics)                           │
│           ├─────────── Celery (Task Metrics)                             │
│           ├─────────── PostgreSQL Exporter                               │
│           ├─────────── Redis Exporter                                    │
│           └─────────── Container Metrics                                 │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Django Web Service (3 Replicas)
```
┌────────────────────────────────────┐
│      Django Web Container          │
├────────────────────────────────────┤
│ ✓ Gunicorn ASGI Server             │
│ ✓ Uvicorn Workers (2)              │
│ ✓ WebSocket Support (Channels)     │
│ ✓ Health Check: /health/           │
│ ✓ Auto-restart on failure          │
│ ✓ Resource Limits: 2 CPU, 2GB RAM │
│ ✓ Update Strategy: Rolling         │
└────────────────────────────────────┘
    │
    ├─▶ Database Connection Pool
    ├─▶ Redis Connection Pool
    ├─▶ Static Files Volume
    └─▶ Media Files Volume
```

### Celery Workers (2 Replicas)
```
┌────────────────────────────────────┐
│    Celery Worker Container         │
├────────────────────────────────────┤
│ ✓ Background Task Processing       │
│ ✓ Concurrency: Auto-detected       │
│ ✓ Task Retry Logic                 │
│ ✓ Health Check: Celery Inspect     │
│ ✓ Auto-restart on failure          │
│ ✓ Resource Limits: 1.5 CPU, 1.5GB │
│ ✓ Metrics: Port 9808               │
└────────────────────────────────────┘
    │
    ├─▶ Redis (Task Queue)
    ├─▶ Database (Results)
    └─▶ Media Files Volume
```

### Data Layer
```
┌───────────────────────┐    ┌──────────────────────┐
│   PostgreSQL 15       │    │      Redis 7         │
│   with pgvector       │    │                      │
├───────────────────────┤    ├──────────────────────┤
│ ✓ Persistent Volume   │    │ ✓ In-Memory Cache    │
│ ✓ Optimized Config    │    │ ✓ Celery Broker      │
│ ✓ Connection Pool     │    │ ✓ Session Store      │
│ ✓ Auto Backup Ready   │    │ ✓ LRU Eviction       │
│ ✓ Health Monitored    │    │ ✓ Persistence: AOF   │
│ ✓ Max Conn: 200       │    │ ✓ Max Memory: 512MB  │
└───────────────────────┘    └──────────────────────┘
```

## High Availability Features

### Automatic Failover
```
Normal Operation:
┌──────┐  ┌──────┐  ┌──────┐
│Web #1│  │Web #2│  │Web #3│  ← All serving traffic
└──────┘  └──────┘  └──────┘

Container Crash:
┌──────┐  ┌──────┐  ┌──────┐
│Web #1│  │  ✗   │  │Web #3│  ← #2 crashes
└──────┘  └──────┘  └──────┘
    ↓
┌──────┐  ┌──────┐  ┌──────┐
│Web #1│  │Web #2│  │Web #3│  ← Swarm auto-restarts #2
└──────┘  └──────┘  └──────┘
              ✓
         (Recovered)

During recovery:
- Traffic continues via #1 and #3
- No service interruption
- Health checks verify recovery
```

### Rolling Updates
```
Step 1: Start new replica
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│Old #1│  │Old #2│  │Old #3│  │New #1│
└──────┘  └──────┘  └──────┘  └──────┘
                                  ↓
                            Health Check
                                  ↓
Step 2: Replace old replica      ✓
┌──────┐  ┌──────┐  ┌──────┐
│New #1│  │Old #2│  │Old #3│
└──────┘  └──────┘  └──────┘

Step 3: Continue rolling
┌──────┐  ┌──────┐  ┌──────┐
│New #1│  │New #2│  │Old #3│
└──────┘  └──────┘  └──────┘

Step 4: Complete
┌──────┐  ┌──────┐  ┌──────┐
│New #1│  │New #2│  │New #3│
└──────┘  └──────┘  └──────┘
```

## Traffic Flow

### HTTP Request Flow
```
1. External Request
   │
   ▼
2. Swarm Ingress Load Balancer
   │ (Round-robin DNS)
   │
   ├─▶ Django Web #1
   ├─▶ Django Web #2
   └─▶ Django Web #3
       │
       ├─▶ PostgreSQL (if needed)
       ├─▶ Redis (cache lookup)
       └─▶ Celery (async tasks)
```

### WebSocket Flow
```
1. WebSocket Connection Request
   │
   ▼
2. Swarm Load Balancer
   │ (Sticky session via VIP)
   │
   ▼
3. Django Web Container
   │ (Channels/Daphne)
   │
   ├─▶ Redis (Channel Layer)
   └─▶ Database (Authentication)
```

### Background Task Flow
```
1. Django creates task
   │
   ▼
2. Task queued in Redis
   │
   ▼
3. Celery Worker picks up task
   │ (First available worker)
   │
   ├─▶ Celery Worker #1
   └─▶ Celery Worker #2
       │
       ├─▶ Database (task data)
       ├─▶ External APIs
       └─▶ Media Files (if needed)
```

## Health Check Flow

```
Every 30 seconds:

Swarm Health Monitor
    │
    ├─▶ Check Django /health/
    │   └─▶ Database: OK?
    │   └─▶ Redis: OK?
    │   └─▶ Response: 200 = Healthy
    │
    ├─▶ Check PostgreSQL
    │   └─▶ pg_isready
    │
    ├─▶ Check Redis
    │   └─▶ redis-cli ping
    │
    └─▶ Check Celery Workers
        └─▶ celery inspect ping

If any fail 3 times in a row:
    ↓
Container marked unhealthy
    ↓
Swarm starts replacement
    ↓
Old container stopped
    ↓
Service continues (other replicas)
```

## Resource Allocation

```
Total Cluster Resources:
┌────────────────────────────────────────┐
│  CPU: 16 cores                         │
│  RAM: 32 GB                            │
│  Disk: 500 GB                          │
└────────────────────────────────────────┘
         │
         ├─▶ Django Web (3×)
         │   CPU: 6 cores max (2×3)
         │   RAM: 6 GB max (2×3)
         │
         ├─▶ Celery Workers (2×)
         │   CPU: 3 cores max (1.5×2)
         │   RAM: 3 GB max (1.5×2)
         │
         ├─▶ PostgreSQL
         │   CPU: 2 cores max
         │   RAM: 2 GB max
         │
         ├─▶ Redis
         │   CPU: 1 core max
         │   RAM: 768 MB max
         │
         └─▶ Monitoring Stack
             CPU: 2 cores max
             RAM: 1.5 GB max

Reserved vs Limits:
- Reserved: Guaranteed minimum
- Limits: Maximum allowed
- Prevents resource exhaustion
```

## Network Topology

```
┌─────────────────────────────────────────────────┐
│         External Network                         │
│         (Internet)                               │
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Firewall/Router    │
         │  Port Forwarding:   │
         │  - 80 → 8000        │
         │  - 443 → 8000 (SSL) │
         └─────────┬───────────┘
                   │
         ┌─────────▼──────────────┐
         │  Swarm Ingress Network  │
         │  (Routing Mesh)         │
         └─────────┬───────────────┘
                   │
         ┌─────────▼──────────────┐
         │  Overlay Network        │
         │  pilito_network         │
         │  10.0.10.0/24          │
         └─────────┬───────────────┘
                   │
    ┌──────────────┼──────────────────┐
    │              │                   │
Services      Services           Services
(Manager)     (Worker 1)       (Worker 2)
```

## Disaster Recovery Architecture

```
Primary Site                    Backup
┌────────────────┐             ┌────────────────┐
│ Swarm Cluster  │             │  Backup Store  │
│                │             │                │
│ ┌────────────┐ │             │ ┌────────────┐ │
│ │ PostgreSQL │─┼────backup───▶ │ Daily DB   │ │
│ └────────────┘ │             │ │ Snapshots  │ │
│                │             │ └────────────┘ │
│ ┌────────────┐ │             │                │
│ │   Media    │─┼────backup───▶ ┌────────────┐ │
│ │   Files    │ │             │ │ Media      │ │
│ └────────────┘ │             │ │ Backups    │ │
│                │             │ └────────────┘ │
│ ┌────────────┐ │             │                │
│ │  Config    │─┼────backup───▶ ┌────────────┐ │
│ │   Files    │ │             │ │ Config     │ │
│ └────────────┘ │             │ │ Backups    │ │
└────────────────┘             └────────────────┘
```

## Scaling Scenarios

### Low Traffic (Development)
```
┌──────┐  ┌────┐  ┌────┐
│Web #1│  │DB  │  │Redis│
└──────┘  └────┘  └────┘
Cost: $50/month
RPS: ~100
```

### Medium Traffic (Small Production)
```
┌──────┐┌──────┐┌──────┐
│Web #1││Web #2││Web #3│  ← 3 replicas
└──────┘└──────┘└──────┘
┌──────┐┌──────┐
│Celery││Celery│           ← 2 workers
└──────┘└──────┘
Cost: $200/month
RPS: ~1000
```

### High Traffic (Large Production)
```
┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐
│Web #1││Web #2││Web #3││Web #4││Web #5│
└──────┘└──────┘└──────┘└──────┘└──────┘
┌──────┐┌──────┐┌──────┐┌──────┐
│Celery││Celery││Celery││Celery│
└──────┘└──────┘└──────┘└──────┘
Cost: $500/month
RPS: ~10,000
```

---

## Summary

This architecture provides:

✅ **No Single Point of Failure**  
✅ **Automatic Recovery from Crashes**  
✅ **Zero-Downtime Deployments**  
✅ **Horizontal Scalability**  
✅ **Health Monitoring**  
✅ **Load Balancing**  
✅ **Resource Management**  
✅ **Easy Maintenance**  

**Result**: Production-ready, highly available Django application infrastructure.

