# Monitoring Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd src
pip install -r requirements/base.txt
```

### Step 2: Start the Stack

```bash
# Start all services including monitoring
docker-compose up -d

# Or just monitoring services if app is already running
docker-compose up -d prometheus grafana redis_exporter postgres_exporter
```

### Step 3: Access Dashboards

Open in your browser:

- **Grafana Dashboard**: http://localhost:3001
  - Username: `admin`
  - Password: `admin`
  
- **Prometheus UI**: http://localhost:9090

- **Metrics Endpoint**: http://localhost:8000/api/v1/metrics

### Step 4: View Your First Dashboard

1. Go to http://localhost:3001
2. Login with `admin`/`admin`
3. Navigate to **Dashboards** → **Fiko Backend - Overview Dashboard**
4. You should see live metrics flowing in!

## 📊 What You'll See

### Key Metrics Available Immediately:

✅ **HTTP Requests** - Request rate, response times, status codes  
✅ **Database** - Query rates, connection count, performance  
✅ **Redis** - Memory usage, cache hit rates  
✅ **Celery** - Task execution, queue length, failures  
✅ **System** - CPU, memory usage  
✅ **Business Metrics** - AI requests, workflows, billing  

## 🔍 Quick Checks

### Is Everything Working?

```bash
# Check all monitoring services are up
docker-compose ps prometheus grafana redis_exporter postgres_exporter

# Test metrics endpoint
curl http://localhost:8000/api/v1/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

### Generate Some Traffic

```bash
# Make some API requests to generate metrics
for i in {1..10}; do
  curl http://localhost:8000/api/v1/usr/
  sleep 1
done

# Check metrics are being collected
curl http://localhost:8000/api/v1/metrics | grep django_http_requests_total
```

## 🎯 Common PromQL Queries

Try these in Prometheus (http://localhost:9090):

**Request rate (last 5 min):**
```promql
rate(django_http_requests_total[5m])
```

**Error rate:**
```promql
rate(django_http_responses_total_by_status_total{status=~"5.."}[5m])
```

**Average response time:**
```promql
rate(django_http_request_duration_seconds_sum[5m]) / rate(django_http_request_duration_seconds_count[5m])
```

**Database queries per second:**
```promql
rate(django_db_queries_total[5m])
```

**Redis memory usage:**
```promql
redis_memory_used_bytes / redis_memory_max_bytes * 100
```

**Celery queue length:**
```promql
sum(celery_queue_length) by (queue_name)
```

## 🚨 Alerts

Pre-configured alerts are monitoring:

- High error rates (>5%)
- Slow response times (p95 > 2s)
- Service downtime (Postgres, Redis, Celery)
- High resource usage (CPU, Memory, Connections)
- Celery queue backlogs
- Database deadlocks

View active alerts in Prometheus: http://localhost:9090/alerts

## 🛠 Troubleshooting

### Grafana shows "No Data"

1. Check Prometheus is running: `docker-compose ps prometheus`
2. Check datasource in Grafana → Configuration → Data Sources
3. Verify metrics endpoint: `curl http://localhost:8000/api/v1/metrics`

### Metrics endpoint returns 404

1. Check Django monitoring app is in `INSTALLED_APPS`
2. Check URL is configured in `core/urls.py`
3. Restart Django: `docker-compose restart web`

### Celery metrics not showing

1. Check Celery worker is using new start script:
   ```bash
   docker-compose logs celery_worker | grep "Prometheus Exporter"
   ```
2. Rebuild if needed: `docker-compose up -d --build celery_worker`

## 📈 Next Steps

1. **Customize Dashboards** - Create panels for your specific metrics
2. **Set Up Alerting** - Configure Alertmanager for notifications
3. **Add Business Metrics** - Instrument your code with custom metrics
4. **Production Setup** - Enable authentication, HTTPS, backup

## 📚 Full Documentation

See [PROMETHEUS_GRAFANA_SETUP.md](./PROMETHEUS_GRAFANA_SETUP.md) for:
- Complete architecture overview
- All available metrics
- Custom metrics guide
- Production recommendations
- Advanced troubleshooting

## 🎓 Learning Resources

- **PromQL Tutorial**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Grafana Dashboards**: https://grafana.com/docs/grafana/latest/dashboards/
- **Best Practices**: https://prometheus.io/docs/practices/naming/

---

**Need Help?** Check the logs:
```bash
docker-compose logs prometheus
docker-compose logs grafana
```

