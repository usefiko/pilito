# 🚀 Deploy Stripe Migration to Production

## Problem
The migration file `0006_add_stripe_fields.py` needs to be deployed to your production server.

## Solution (2 Methods)

### Method 1: Git Deploy (Recommended)

```bash
# On your local machine
cd /Users/nima/Projects/Fiko-Backend

# Add the migration file
git add src/billing/migrations/0006_add_stripe_fields.py
git add src/billing/models.py
git add src/billing/services/stripe_service.py

# Commit
git commit -m "Add Stripe integration fields to billing models"

# Push to repository
git push origin main

# SSH to your server
ssh ubuntu@your-server-ip

# Pull latest changes
cd /path/to/Fiko-Backend
git pull origin main

# Restart Docker containers
docker-compose restart

# Run migrations inside container
docker-compose exec web python manage.py migrate

# Verify
docker-compose exec web python manage.py showmigrations billing
```

### Method 2: Direct Copy (Quick but not recommended)

If you need to fix it immediately without git:

```bash
# On your local machine
cd /Users/nima/Projects/Fiko-Backend

# Copy file to server
scp src/billing/migrations/0006_add_stripe_fields.py \
    ubuntu@your-server-ip:/path/to/Fiko-Backend/src/billing/migrations/

# SSH to server
ssh ubuntu@your-server-ip

# Restart containers
cd /path/to/Fiko-Backend
docker-compose restart

# Run migration
docker-compose exec web python manage.py migrate
```

### Method 3: If Using Direct Docker (No docker-compose)

```bash
# Find your running container
docker ps

# Copy file to container
docker cp src/billing/migrations/0006_add_stripe_fields.py \
    YOUR_CONTAINER_ID:/app/billing/migrations/

# Run migration
docker exec -it YOUR_CONTAINER_ID python manage.py migrate
```

---

## ✅ Verify Migration Works

```bash
# Check migration status
docker-compose exec web python manage.py showmigrations billing

# Should show:
# [X] 0006_add_stripe_fields
```

---

## 🔧 After Migration is Applied

Run the Django shell to link your Stripe prices:

```bash
docker-compose exec web python manage.py shell
```

```python
from billing.models import FullPlan

# Link monthly price
monthly = FullPlan.objects.filter(is_yearly=False).first()
if monthly:
    monthly.stripe_price_id = 'price_1S0dwrKkH1LI50QC2GhtfzN4'
    monthly.save()
    print(f'✅ Monthly: {monthly.name}')

# Link yearly price
yearly = FullPlan.objects.filter(is_yearly=True).first()
if yearly:
    yearly.stripe_price_id = 'price_1S0dxYKkH1LI50QCEqPZJ6Jq'
    yearly.save()
    print(f'✅ Yearly: {yearly.name}')

exit()
```

---

## 🎯 Complete Deployment Checklist

- [ ] Commit and push migration file
- [ ] Pull changes on production server
- [ ] Restart Docker containers
- [ ] Run migrations: `docker-compose exec web python manage.py migrate`
- [ ] Link Stripe price IDs (Django shell)
- [ ] Test checkout session creation
- [ ] Verify webhook receiving events

---

## 🆘 Troubleshooting

### Error: "Migration has no Migration class"
**Solution**: The file was corrupted or incomplete. Re-copy the file from local machine.

### Error: "No such file or directory"
**Solution**: Make sure the path is correct. The file should be in:
`/app/billing/migrations/0006_add_stripe_fields.py` (inside container)

### Error: "Conflicting migrations"
**Solution**: 
```bash
docker-compose exec web python manage.py makemigrations --merge
docker-compose exec web python manage.py migrate
```

---

**Recommended**: Use Git method (Method 1) for proper version control and deployment.

