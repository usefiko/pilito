# 🔧 Monitoring Ports Access Fix

## Problem Summary

The monitoring services (Grafana, Prometheus, etc.) are running correctly in Docker containers but are not accessible from outside the EC2 instance. Only port 8000 is accessible.

**Error in logs:**
```
Invalid HTTP_HOST header: 'web:8000'. You may need to add 'web' to ALLOWED_HOSTS.
Bad Request: /api/v1/metrics
```

## Root Causes

### 1. ✅ FIXED: Django ALLOWED_HOSTS Issue
- **Problem:** Django was rejecting internal Docker requests from Prometheus
- **Solution:** Added Docker container hostnames to `ALLOWED_HOSTS`
- **Status:** Fixed in `src/core/settings/production.py`

### 2. ⚠️ TO FIX: AWS Security Group Blocking Ports
- **Problem:** AWS Security Group only allows port 8000
- **Blocked Ports:**
  - `3001` - Grafana Dashboard
  - `9090` - Prometheus UI
  - `9121` - Redis Exporter
  - `9187` - PostgreSQL Exporter
  - `9808` - Celery Worker Metrics

## Solutions

### Option 1: Open Ports in AWS Security Group (Quick but Less Secure)

#### A. Using AWS Console (Easiest)

1. Go to [AWS EC2 Console](https://console.aws.amazon.com/ec2/)
2. Navigate to **Security Groups** (left sidebar under "Network & Security")
3. Find the security group attached to instance `3.12.166.146`
4. Click **"Edit inbound rules"**
5. Add these rules:

| Type | Port | Source | Description |
|------|------|--------|-------------|
| Custom TCP | 3001 | 0.0.0.0/0 | Grafana Dashboard |
| Custom TCP | 9090 | 0.0.0.0/0 | Prometheus UI |
| Custom TCP | 9121 | 0.0.0.0/0 | Redis Exporter |
| Custom TCP | 9187 | 0.0.0.0/0 | PostgreSQL Exporter |
| Custom TCP | 9808 | 0.0.0.0/0 | Celery Worker Metrics |

6. Click **"Save rules"**

#### B. Using AWS CLI (Automated)

We've provided a script to automate this:

```bash
# Make script executable
chmod +x fix_monitoring_ports.sh

# Run the script (will auto-detect instance if run on EC2)
./fix_monitoring_ports.sh

# Or specify instance/security group manually
./fix_monitoring_ports.sh i-xxxxx sg-xxxxx
```

**⚠️ Security Warning:**
- `0.0.0.0/0` opens ports to the entire internet
- For production, use your specific IP: `YOUR_IP/32`
- Or use SSH tunneling (Option 2 - more secure)

### Option 2: SSH Tunneling (Recommended for Production - More Secure)

Instead of opening ports publicly, use SSH tunneling to access services securely:

```bash
ssh -L 3001:localhost:3001 \
    -L 9090:localhost:9090 \
    -L 9121:localhost:9121 \
    -L 9187:localhost:9187 \
    -L 9808:localhost:9808 \
    ubuntu@3.12.166.146
```

Then access services on your **local machine**:
- **Grafana:** http://localhost:3001
- **Prometheus:** http://localhost:9090
- **Redis Exporter:** http://localhost:9121
- **PostgreSQL Exporter:** http://localhost:9187
- **Celery Metrics:** http://localhost:9808

**Advantages:**
- ✅ No public exposure of monitoring ports
- ✅ Encrypted connection through SSH
- ✅ No AWS Security Group changes needed
- ✅ Best practice for production

### Option 3: VPN or Bastion Host (Enterprise)

For enterprise environments:
1. Set up AWS VPN or AWS Client VPN
2. Or use a bastion host with restricted access
3. Configure security groups to only allow access from VPN/bastion

## What We Fixed

### 1. Updated ALLOWED_HOSTS

**File:** `src/core/settings/production.py`

```python
ALLOWED_HOSTS = [
    'api.fiko.net',
    'fiko.net', 
    'app.fiko.net',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '18.119.134.7',
    '172.31.8.229',
    '3.12.166.146',
    'ec2-3-12-166-146.us-east-2.compute.amazonaws.com',
    # Docker internal network hostnames for monitoring
    'web',                    # ✅ NEW
    'django_app',             # ✅ NEW
    'prometheus',             # ✅ NEW
    'grafana',                # ✅ NEW
    'celery_worker',          # ✅ NEW
    'celery_beat',            # ✅ NEW
    'redis_exporter',         # ✅ NEW
    'postgres_exporter',      # ✅ NEW
]
```

This allows Prometheus to scrape metrics from Django without getting rejected.

## Deployment Steps

### Step 1: Deploy the Fixed Code

```bash
# The fix will be deployed automatically via GitHub Actions
git add .
git commit -m "Fix monitoring ports access and ALLOWED_HOSTS"
git push origin main
```

Or manually on the server:

```bash
# SSH to server
ssh ubuntu@3.12.166.146

# Navigate to project
cd /home/ubuntu/fiko-backend

# Pull latest changes
git pull origin main

# Restart containers
docker-compose down
docker-compose up -d

# Verify containers are running
docker ps
```

### Step 2: Choose Your Access Method

**For Development/Testing:**
- Use **Option 1A** (AWS Console) - Quick and easy

**For Production:**
- Use **Option 2** (SSH Tunneling) - Most secure

**For Enterprise:**
- Use **Option 3** (VPN/Bastion) - Best for teams

## Verification

### Test Internal Metrics (should work now)

```bash
# SSH to server
ssh ubuntu@3.12.166.146

# Test metrics endpoint from inside Docker network
docker exec django_app curl -s http://web:8000/api/v1/metrics | head -20

# Check Prometheus is scraping successfully
docker logs prometheus | grep "Scrape"
```

### Test External Access (after opening ports)

```bash
# Test from your local machine
curl http://3.12.166.146:3001  # Grafana
curl http://3.12.166.146:9090  # Prometheus
curl http://3.12.166.146:9121/metrics  # Redis Exporter
curl http://3.12.166.146:9187/metrics  # PostgreSQL Exporter
curl http://3.12.166.146:9808/metrics  # Celery Metrics
```

## Service URLs

### After Opening Ports (Option 1)
- **Grafana Dashboard:** http://3.12.166.146:3001
  - Username: `admin`
  - Password: `admin`
- **Prometheus UI:** http://3.12.166.146:9090
- **Redis Exporter:** http://3.12.166.146:9121/metrics
- **PostgreSQL Exporter:** http://3.12.166.146:9187/metrics
- **Celery Worker:** http://3.12.166.146:9808/metrics

### Using SSH Tunneling (Option 2)
- **Grafana Dashboard:** http://localhost:3001
- **Prometheus UI:** http://localhost:9090
- **Redis Exporter:** http://localhost:9121/metrics
- **PostgreSQL Exporter:** http://localhost:9187/metrics
- **Celery Worker:** http://localhost:9808/metrics

## Troubleshooting

### Issue: Still getting "Invalid HTTP_HOST" error

**Solution:**
```bash
# Restart Django container
docker-compose restart web

# Verify ALLOWED_HOSTS
docker exec django_app python manage.py shell -c "from django.conf import settings; print(settings.ALLOWED_HOSTS)"
```

### Issue: Ports still blocked after opening Security Group

**Check:**
1. Verify Security Group is attached to instance
2. Check Network ACLs (should allow all by default)
3. Verify Docker port mappings: `docker ps`
4. Check if firewall is running on EC2: `sudo ufw status`

### Issue: SSH tunnel disconnects

**Solution:**
```bash
# Use autossh for persistent tunnel
autossh -M 0 -N \
    -L 3001:localhost:3001 \
    -L 9090:localhost:9090 \
    -L 9121:localhost:9121 \
    -L 9187:localhost:9187 \
    -L 9808:localhost:9808 \
    ubuntu@3.12.166.146
```

## Security Best Practices

### ❌ Don't Do This in Production:
- Don't use `0.0.0.0/0` for monitoring ports
- Don't expose Prometheus/Grafana to the internet without authentication
- Don't leave default Grafana password (`admin/admin`)

### ✅ Do This Instead:
- Use SSH tunneling for secure access
- Use VPN or bastion host for team access
- Change Grafana default password
- Use IP whitelisting (your office IP)
- Enable authentication on Prometheus/Grafana
- Use HTTPS with SSL certificates

## Next Steps

1. ✅ Deploy the ALLOWED_HOSTS fix
2. 🔧 Choose your access method (SSH tunnel recommended)
3. 🔒 Update Grafana password
4. 📊 Configure Grafana dashboards
5. 🚨 Set up Prometheus alerts

## Quick Reference

### Restart Monitoring Stack
```bash
docker-compose restart prometheus grafana redis_exporter postgres_exporter celery_worker
```

### View Logs
```bash
docker logs prometheus
docker logs grafana
docker logs django_app
```

### Check Metrics
```bash
# Django metrics
curl http://3.12.166.146:8000/api/v1/metrics

# All exporters
curl http://3.12.166.146:9121/metrics  # Redis
curl http://3.12.166.146:9187/metrics  # PostgreSQL
curl http://3.12.166.146:9808/metrics  # Celery
```

