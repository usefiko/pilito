# Fiko Backend Monitoring Stack

Complete Prometheus + Grafana monitoring solution for the Fiko Backend application.

## 📁 Directory Structure

```
monitoring/
├── prometheus/
│   ├── prometheus.yml          # Prometheus configuration
│   └── alerts.yml              # Alert rules
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/        # Auto-configured datasources
│   │   │   └── prometheus.yml
│   │   └── dashboards/         # Dashboard provisioning
│   │       └── default.yml
│   └── dashboards/             # Dashboard JSON files
│       └── fiko-backend-overview.json
└── README.md                   # This file
```

## 🚀 Quick Start

```bash
# Start monitoring stack
docker-compose up -d prometheus grafana redis_exporter postgres_exporter

# Access Grafana
open http://localhost:3001
# Login: admin / admin

# Access Prometheus
open http://localhost:9090
```

## 📊 Included Components

### Prometheus (Port 9090)
- Time-series database for metrics
- Scrapes metrics from all services
- 30-day data retention
- Alert evaluation engine

### Grafana (Port 3001)
- Visualization platform
- Pre-configured dashboards
- Auto-provisioned Prometheus datasource
- Real-time monitoring

### Exporters
- **Redis Exporter** (Port 9121) - Redis metrics
- **PostgreSQL Exporter** (Port 9187) - Database metrics
- **Celery Exporter** (Port 9808) - Task queue metrics

### Django Metrics App
- Custom middleware for HTTP metrics
- Database query tracking
- Business-specific metrics
- Exposed at `/api/v1/metrics`

## 📈 Available Dashboards

### Fiko Backend Overview
Comprehensive dashboard showing:
- HTTP request rates and response times
- Error rates and status codes
- Database query performance
- Redis memory and operations
- Celery task execution and queues
- System resources (CPU, memory)
- AI model requests
- Workflow executions
- Business metrics

**UID:** `fiko-backend-overview`

## 🔍 Metrics Collected

### Application Metrics
- `django_http_requests_total` - HTTP requests
- `django_http_request_duration_seconds` - Response times
- `django_db_queries_total` - Database queries
- `django_ai_requests_total` - AI model calls
- `django_workflow_executions_total` - Workflow runs
- `django_billing_transactions_total` - Billing events

### Infrastructure Metrics
- `redis_memory_used_bytes` - Redis memory
- `pg_stat_database_*` - PostgreSQL stats
- `celery_tasks_total` - Celery tasks
- `celery_queue_length` - Queue depth

### System Metrics
- `django_system_memory_usage_bytes` - Memory usage
- `django_system_cpu_usage_percent` - CPU usage
- `process_*` - Process metrics

## 🚨 Pre-configured Alerts

### Critical
- Service down (Django, Postgres, Redis, Celery)
- High error rate (>5%)
- Redis rejecting connections

### Warning
- High response times (p95 > 2s)
- High memory usage (>90%)
- High connection count
- Large Celery queue backlog

## 🛠 Configuration

### Prometheus Configuration
Edit `prometheus/prometheus.yml` to:
- Change scrape intervals
- Add new targets
- Modify retention period

### Grafana Provisioning
- Datasources: `grafana/provisioning/datasources/`
- Dashboards: `grafana/provisioning/dashboards/`
- Dashboard JSON: `grafana/dashboards/`

### Alert Rules
Edit `prometheus/alerts.yml` to:
- Add new alerts
- Modify thresholds
- Change alert severity

## 🔐 Security

**Default Credentials:**
- Grafana: admin / admin (change immediately!)

**Production Recommendations:**
- Change default passwords
- Restrict port access
- Enable HTTPS
- Set up proper authentication

## 📚 Documentation

- **Quick Start**: See `../MONITORING_QUICK_START.md`
- **Full Guide**: See `../PROMETHEUS_GRAFANA_SETUP.md`
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/

## 🐛 Troubleshooting

### Check Service Health
```bash
docker-compose ps prometheus grafana
docker-compose logs prometheus grafana
```

### Verify Metrics Collection
```bash
curl http://localhost:8000/api/v1/metrics
curl http://localhost:9090/api/v1/targets
```

### Test Alert Rules
```bash
curl http://localhost:9090/api/v1/rules
curl http://localhost:9090/api/v1/alerts
```

## 🔄 Maintenance

### Backup Dashboards
Dashboards are version-controlled in this directory.
Custom dashboards should be exported and saved here.

### Data Retention
Default: 30 days  
Configure in `docker-compose.yml`:
```yaml
command:
  - '--storage.tsdb.retention.time=30d'
```

### Update Components
```bash
docker-compose pull prometheus grafana redis_exporter postgres_exporter
docker-compose up -d prometheus grafana redis_exporter postgres_exporter
```

## 📊 Creating Custom Dashboards

1. Create in Grafana UI
2. Export JSON (Dashboard → Share → Export)
3. Save to `grafana/dashboards/`
4. Restart Grafana to auto-load

## 🎯 Common Queries

**Request Rate:**
```promql
rate(django_http_requests_total[5m])
```

**Error Rate:**
```promql
rate(django_http_responses_total_by_status_total{status=~"5.."}[5m])
```

**P95 Response Time:**
```promql
histogram_quantile(0.95, rate(django_http_request_duration_seconds_bucket[5m]))
```

**Queue Length:**
```promql
sum(celery_queue_length) by (queue_name)
```

---

**Version:** 1.0.0  
**Last Updated:** October 8, 2025

