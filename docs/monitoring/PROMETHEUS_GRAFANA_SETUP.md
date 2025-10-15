# Prometheus + Grafana Monitoring Setup

## Overview

This document describes the comprehensive monitoring stack implemented for the Fiko Backend application using Prometheus and Grafana.

## Architecture

The monitoring stack consists of:

1. **Prometheus** - Time-series database and metrics collector
2. **Grafana** - Visualization and dashboarding platform
3. **Redis Exporter** - Exposes Redis metrics
4. **PostgreSQL Exporter** - Exposes PostgreSQL metrics
5. **Django Metrics App** - Custom Django middleware for application metrics
6. **Celery Prometheus Exporter** - Exposes Celery task metrics

## Components

### 1. Prometheus (Port 9090)

Prometheus scrapes metrics from various endpoints:
- **Django App**: `http://web:8000/api/v1/metrics`
- **Redis**: `http://redis_exporter:9121`
- **PostgreSQL**: `http://postgres_exporter:9187`
- **Celery**: `http://celery_worker:9808`

**Configuration Files:**
- `monitoring/prometheus/prometheus.yml` - Main configuration
- `monitoring/prometheus/alerts.yml` - Alert rules

### 2. Grafana (Port 3001)

Web-based visualization platform with pre-configured dashboards.

**Default Credentials:**
- Username: `admin`
- Password: `admin` (change on first login)

**Dashboards:**
- **Fiko Backend Overview** - Comprehensive system overview

### 3. Django Monitoring App

Custom Django app that collects and exposes application metrics.

**Key Metrics Collected:**
- HTTP request/response metrics (rate, duration, status codes)
- Database query metrics (count, duration, type)
- Cache hit/miss rates
- Authentication attempts
- WebSocket connection metrics
- Celery task metrics
- AI model request metrics
- Billing transaction metrics
- Workflow execution metrics
- User activity metrics
- Business-specific metrics (Academy, Instagram, etc.)

**Files:**
- `src/monitoring/metrics.py` - Metric definitions
- `src/monitoring/middleware.py` - Request/response instrumentation
- `src/monitoring/views.py` - Metrics endpoint
- `src/monitoring/urls.py` - URL configuration

## Quick Start

### 1. Install Dependencies

```bash
cd src
pip install -r requirements/base.txt
```

### 2. Start the Monitoring Stack

```bash
docker-compose up -d prometheus grafana redis_exporter postgres_exporter
```

### 3. Restart Application Services

To enable metrics collection in Django and Celery:

```bash
docker-compose up -d --build web celery_worker
```

### 4. Access Dashboards

- **Prometheus UI**: http://localhost:9090
- **Grafana**: http://localhost:3001

## Metrics Endpoints

### Django Application Metrics

**Endpoint:** `http://localhost:8000/api/v1/metrics`

All HTTP requests are automatically instrumented through middleware.

### Health Check

**Endpoint:** `http://localhost:8000/api/v1/metrics/health`

Returns `OK` if the application is running.

## Key Metrics

### HTTP Metrics

- `django_http_requests_total` - Total HTTP requests by method, endpoint, and status
- `django_http_request_duration_seconds` - Request duration histogram
- `django_http_responses_total_by_status_total` - Responses by status code
- `django_http_request_size_bytes` - Request size histogram
- `django_http_response_size_bytes` - Response size histogram

### Database Metrics

- `django_db_queries_total` - Total database queries by type
- `django_db_query_duration_seconds` - Query duration histogram
- `django_db_connections_active` - Active database connections
- `pg_stat_database_*` - PostgreSQL specific metrics (from exporter)

### Redis Metrics

- `redis_memory_used_bytes` - Memory usage
- `redis_connected_clients` - Connected clients
- `redis_commands_processed_total` - Total commands processed
- `redis_keyspace_hits_total` - Cache hits
- `redis_keyspace_misses_total` - Cache misses

### Celery Metrics

- `celery_tasks_total` - Total tasks by name and state
- `celery_task_duration_seconds` - Task duration histogram
- `celery_queue_length` - Tasks in queue by queue name
- `celery_workers` - Number of active workers

### AI Model Metrics

- `django_ai_requests_total` - AI requests by model and status
- `django_ai_request_duration_seconds` - AI request duration
- `django_ai_tokens_consumed_total` - Total tokens consumed

### Workflow Metrics

- `django_workflow_executions_total` - Workflow executions by status
- `django_workflow_execution_duration_seconds` - Execution duration
- `django_workflow_actions_total` - Actions executed by type

### System Metrics

- `django_system_memory_usage_bytes` - Memory usage (RSS, VMS)
- `django_system_cpu_usage_percent` - CPU usage percentage
- `process_*` - Standard process metrics

## Alerting

Prometheus alerts are configured in `monitoring/prometheus/alerts.yml`.

### Critical Alerts

- **DjangoHighErrorRate** - 5xx error rate > 5%
- **PostgresDown** - Database unavailable
- **RedisDown** - Redis unavailable
- **CeleryWorkerDown** - Worker unavailable

### Warning Alerts

- **DjangoHighResponseTime** - p95 > 2 seconds
- **PostgresHighConnections** - Connections > 80
- **RedisHighMemoryUsage** - Memory usage > 90%
- **CeleryHighTaskFailureRate** - Task failures > 10%

## Custom Metrics

### Adding New Metrics

1. Define the metric in `src/monitoring/metrics.py`:

```python
from prometheus_client import Counter

my_custom_metric = Counter(
    'django_my_custom_metric_total',
    'Description of my metric',
    ['label1', 'label2']
)
```

2. Use it in your code:

```python
from monitoring import metrics

metrics.my_custom_metric.labels(label1='value1', label2='value2').inc()
```

### Metric Types

- **Counter** - Monotonically increasing value (requests, errors)
- **Gauge** - Value that can go up or down (memory, connections)
- **Histogram** - Distribution of values (duration, size)
- **Summary** - Similar to histogram with quantiles

## Dashboard Customization

### Grafana Dashboard Location

Pre-configured dashboards are in:
```
monitoring/grafana/dashboards/
```

### Creating New Dashboards

1. Create dashboard in Grafana UI
2. Export JSON via Dashboard Settings → JSON Model
3. Save to `monitoring/grafana/dashboards/`
4. Restart Grafana to auto-load: `docker-compose restart grafana`

### Useful PromQL Queries

#### Request Rate (per second)
```promql
rate(django_http_requests_total[5m])
```

#### Error Rate (5xx errors per second)
```promql
rate(django_http_responses_total_by_status_total{status=~"5.."}[5m])
```

#### 95th Percentile Response Time
```promql
histogram_quantile(0.95, rate(django_http_request_duration_seconds_bucket[5m]))
```

#### Database Query Rate by Type
```promql
rate(django_db_queries_total[5m])
```

#### Celery Queue Backlog
```promql
sum(celery_queue_length) by (queue_name)
```

## Troubleshooting

### Metrics Not Appearing

1. **Check Django middleware is enabled:**
   ```python
   # In settings/common.py
   MIDDLEWARE = [
       'monitoring.middleware.PrometheusMetricsMiddleware',
       'monitoring.middleware.DatabaseMetricsMiddleware',
       ...
   ]
   ```

2. **Check metrics endpoint is accessible:**
   ```bash
   curl http://localhost:8000/api/v1/metrics
   ```

3. **Check Prometheus is scraping:**
   - Open Prometheus UI: http://localhost:9090
   - Go to Status → Targets
   - All targets should be "UP"

### Grafana Dashboard Not Loading

1. **Check datasource configuration:**
   ```bash
   docker exec -it grafana cat /etc/grafana/provisioning/datasources/prometheus.yml
   ```

2. **Check Grafana logs:**
   ```bash
   docker logs grafana
   ```

3. **Verify Prometheus is accessible from Grafana:**
   ```bash
   docker exec -it grafana curl http://prometheus:9090/-/healthy
   ```

### High Memory Usage

Prometheus stores metrics in memory. To reduce usage:

1. **Decrease retention period** (in `docker-compose.yml`):
   ```yaml
   command:
     - '--storage.tsdb.retention.time=15d'  # Default: 30d
   ```

2. **Reduce scrape frequency** (in `prometheus.yml`):
   ```yaml
   global:
     scrape_interval: 30s  # Default: 15s
   ```

### Celery Metrics Not Working

1. **Check Celery exporter is running:**
   ```bash
   docker exec -it celery_worker ps aux | grep celery_exporter
   ```

2. **Check exporter port is accessible:**
   ```bash
   curl http://localhost:9808/metrics
   ```

3. **Check Celery worker logs:**
   ```bash
   docker logs celery_worker
   ```

## Performance Impact

The monitoring stack has minimal performance impact:

- **Django Middleware**: ~1-2ms per request
- **Metrics Storage**: ~10MB memory per 1000 active time series
- **Prometheus Scraping**: Negligible (pull-based)

## Production Recommendations

### 1. Security

- **Change Grafana admin password** immediately
- **Restrict access** to monitoring ports (9090, 3001)
- **Use HTTPS** for Grafana in production
- **Enable authentication** on Prometheus

### 2. Data Retention

- Set appropriate retention based on storage capacity
- Consider remote storage for long-term metrics (e.g., Thanos, Cortex)

### 3. Alerting

- Configure Alertmanager for alert routing
- Integrate with PagerDuty, Slack, or email
- Set up on-call rotations

### 4. High Availability

For production, consider:
- Multiple Prometheus instances
- Grafana HA setup
- Remote storage backend

## Environment Variables

Add to `.env` file:

```bash
# Monitoring
PROMETHEUS_RETENTION_DAYS=30
GRAFANA_ADMIN_PASSWORD=your-secure-password
ENABLE_METRICS=true
```

## Backup and Restore

### Backup Prometheus Data

```bash
docker run --rm --volumes-from prometheus -v $(pwd):/backup ubuntu tar cvf /backup/prometheus-backup.tar /prometheus
```

### Backup Grafana Dashboards

Dashboards are stored in the repository under `monitoring/grafana/dashboards/`.
To backup custom dashboards:

```bash
docker exec grafana grafana-cli admin export-dashboard > dashboard-backup.json
```

### Restore

```bash
docker run --rm --volumes-from prometheus -v $(pwd):/backup ubuntu bash -c "cd /prometheus && tar xvf /backup/prometheus-backup.tar --strip 1"
```

## Integration with CI/CD

### Health Checks

Add to your deployment pipeline:

```bash
# Wait for services to be healthy
curl -f http://localhost:8000/api/v1/metrics/health || exit 1
curl -f http://localhost:9090/-/healthy || exit 1
```

### Metrics Testing

Test metrics are being collected:

```bash
# Make a test request
curl http://localhost:8000/api/v1/usr/

# Check metric was recorded
curl http://localhost:8000/api/v1/metrics | grep django_http_requests_total
```

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Django Prometheus Client](https://github.com/prometheus/client_python)

## Support

For issues or questions:
1. Check logs: `docker-compose logs prometheus grafana`
2. Review Prometheus targets: http://localhost:9090/targets
3. Check Grafana datasource: Grafana → Configuration → Data Sources

## Changelog

### Version 1.0.0 (Initial Setup)
- Added Prometheus + Grafana stack
- Implemented Django metrics middleware
- Added Redis and PostgreSQL exporters
- Created Celery metrics exporter
- Added comprehensive overview dashboard
- Configured alerting rules
- Created documentation

---

**Last Updated:** October 8, 2025
**Maintainer:** DevOps Team

