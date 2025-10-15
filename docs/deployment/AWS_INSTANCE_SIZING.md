# 🚀 AWS Instance Sizing Guide for Fiko Backend

## Current Configuration: t3.small

**Specs:**
- 2 vCPU
- 2 GB RAM
- $0.0208/hour (~$15/month)

**Status:** ✅ OK for Development/Staging with current limits

---

## Resource Allocation

| Service | CPU | RAM | Purpose |
|---------|-----|-----|---------|
| Django Web | 0.3 | 400MB | ASGI server (Daphne) |
| PostgreSQL | 0.2 | 250MB | Database with pgvector |
| Redis | 0.1 | 80MB | Cache & Celery broker |
| **Celery Worker** | **1.5 (limit)** | **1.5GB (limit)** | All background tasks |
| Celery Beat | 0.1 | 100MB | Task scheduler |
| System | 0.3 | 200MB | OS overhead |
| **Total** | **~2.5** | **~2.53GB** | **Needs bursting!** |

⚠️ **Note:** t3.small uses **CPU credits** for bursting above baseline (20% CPU).

---

## When to Upgrade?

### ⚠️ Upgrade to **t3.medium** if you see:

1. **High CPU Burst Usage:**
   ```bash
   # Check CPU credits
   aws cloudwatch get-metric-statistics --namespace AWS/EC2 \
     --metric-name CPUCreditBalance --dimensions Name=InstanceId,Value=i-xxx
   ```
   - Credits dropping below 50 → Upgrade!

2. **Memory Pressure:**
   ```bash
   # On server
   free -h
   # If "available" < 300MB → Upgrade!
   ```

3. **Slow Response Times:**
   - API response > 2 seconds
   - Crawler hanging frequently
   - AI responses delayed

4. **Production Traffic:**
   - More than 10 active conversations simultaneously
   - Crawling multiple large websites (100+ pages)
   - Heavy workflow automation usage

---

## Instance Comparison

| Instance | vCPU | RAM | Cost/Month | Use Case |
|----------|------|-----|------------|----------|
| **t3.small** | 2 | 2GB | ~$15 | Dev/Staging, light production |
| **t3.medium** | 2 | 4GB | ~$30 | **Production (Recommended)** |
| t3.large | 2 | 8GB | ~$60 | Heavy production |
| t3.xlarge | 4 | 16GB | ~$120 | Enterprise scale |

### 💡 **Recommended for Production: t3.medium**

**Why?**
- 4GB RAM = comfortable headroom
- Same 2 vCPU (enough for most workloads)
- Only $15 more per month
- No memory pressure
- Stable performance under load

---

## How to Upgrade (Zero Downtime)

### Option 1: AWS Console (Easy)

```
1. Stop instance: EC2 Dashboard → Instance → Actions → Stop
2. Wait for "stopped" state
3. Actions → Instance Settings → Change Instance Type
4. Select "t3.medium"
5. Start instance
```

⏱️ Downtime: ~3-5 minutes

### Option 2: AWS CLI

```bash
# Stop instance
aws ec2 stop-instances --instance-ids i-xxxxx

# Wait for stopped
aws ec2 wait instance-stopped --instance-ids i-xxxxx

# Change type
aws ec2 modify-instance-attribute \
  --instance-id i-xxxxx \
  --instance-type t3.medium

# Start instance
aws ec2 start-instances --instance-ids i-xxxxx
```

---

## Monitoring Commands

### On Server (SSH):

```bash
# 1. Memory usage
free -h
docker stats --no-stream

# 2. CPU usage
top -bn1 | head -20

# 3. Check if swap is being used (BAD sign!)
swapon --show
free -h | grep Swap

# 4. Celery worker memory
docker stats celery_worker --no-stream
```

### From AWS Console:

```
CloudWatch → EC2 Metrics:
- CPUUtilization (should be < 80% average)
- CPUCreditBalance (should stay stable)
- StatusCheckFailed (should be 0)
```

---

## Current Limits Applied

### Celery Worker Limits (docker-compose.yml):

```yaml
deploy:
  resources:
    limits:
      cpus: '1.5'      # Max 1.5 CPU cores
      memory: 1536M    # Max 1.5GB RAM
    reservations:
      memory: 512M     # Reserved 512MB
```

### Crawler Limits (code):

- Max pages per website: **30** (reduced from 50)
- Request delay: **2 seconds** (increased from 1s)
- Request timeout: **20 seconds** (reduced from 30s)
- Concurrency: **2 tasks** (already set)

---

## Cost Analysis

| Scenario | Instance | Monthly Cost | When? |
|----------|----------|--------------|-------|
| Development | t3.small | $15 | Testing, staging |
| **Light Production** | **t3.small** | **$15** | **< 50 conversations/day** |
| **Production** | **t3.medium** | **$30** | **50-500 conversations/day** |
| Heavy Production | t3.large | $60 | 500+ conversations/day |

---

## Decision Matrix

### ✅ Stay on t3.small if:
- Development/staging environment
- < 50 active conversations per day
- Limited crawling (< 5 websites)
- Not mission-critical uptime

### 🚀 Upgrade to t3.medium if:
- Production environment
- 50+ conversations per day
- Multiple large websites to crawl
- Need stable performance
- Want peace of mind

---

## Quick Health Check

Run this on your server:

```bash
echo "=== HEALTH CHECK ==="
echo "Memory:"
free -h | grep Mem
echo ""
echo "Swap (should be minimal):"
free -h | grep Swap
echo ""
echo "Docker containers:"
docker stats --no-stream
echo ""
echo "CPU Load (< 2.0 is good for t3.small):"
uptime
```

**Interpretation:**
- Memory available < 300MB → ⚠️ Consider upgrade
- Swap used > 100MB → ❌ Upgrade now!
- Load average > 2.0 → ⚠️ Monitor closely

---

## Contact Support

If you see persistent issues:
1. Check monitoring commands above
2. Review logs: `docker compose logs --tail 100`
3. Consider upgrading instance type
4. Optimize workload (reduce concurrent crawls)

**Remember:** Upgrading from t3.small → t3.medium costs only $15/month more but gives 2x RAM! 💪
