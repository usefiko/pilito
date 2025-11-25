# Project Root Structure

This document explains what files remain in the project root and why.

## Essential Files

### Shell Scripts (`.sh`)

#### `entrypoint.sh` ✅
- **Purpose:** Docker container entrypoint
- **Usage:** Automatically executed when containers start
- **Status:** Required for Docker operations

#### `deploy_to_server.sh` ✅
- **Purpose:** Main deployment script for production server
- **Usage:** Deploy code changes to production via SSH
- **Status:** Active deployment script

### Configuration Files

#### `docker-compose.yml` ✅
- **Purpose:** Docker Compose configuration for development/production
- **Usage:** `docker-compose up`
- **Status:** Required

#### `docker-compose.swarm.yml` ✅
- **Purpose:** Docker Swarm configuration for production
- **Usage:** Swarm deployments
- **Status:** Required

#### `Dockerfile` ✅
- **Purpose:** Docker image build instructions
- **Usage:** `docker build`
- **Status:** Required

#### `Makefile` ✅
- **Purpose:** Common development commands
- **Usage:** `make <command>`
- **Status:** Optional but useful

#### `intent_keywords_complete.sql` ✅
- **Purpose:** SQL file for keywords data
- **Usage:** Database seeding
- **Status:** Required for keywords feature

## Removed Files

### Deleted Shell Scripts ❌

These scripts were removed because they were:
- One-time migration fixes (no longer needed)
- Duplicate functionality (covered by main deploy script)
- Unused/outdated

**Deleted:**
- `comprehensive_migration_fix.sh` - One-time migration fix
- `deploy_fixed_migrations.sh` - One-time migration deployment
- `deploy_safe_migration.sh` - Duplicate of deploy_to_server.sh
- `deploy_keywords_migration.sh` - Old one-time migration
- `fix_migration_on_server.sh` - One-time fix
- `fix_migration_with_password.sh` - One-time fix
- `fix_production_db.sh` - Old fix script
- `monitor_redis_health.sh` - Unused monitoring script
- `update_static_files.sh` - Functionality in deploy script

### Moved Documentation Files ✅

All root-level `.md` files moved to `docs/` folder:
- `AFFILIATE_IMPLEMENTATION_SUMMARY.md` → `docs/`
- `GITHUB_ACTION_FIX_SUMMARY.md` → `docs/`
- `MIGRATION_FIX_README.md` → `docs/`
- `PRODUCTION_FIX_GUIDE.md` → `docs/`

## Directory Structure

```
pilito/
├── entrypoint.sh              # Docker entrypoint (required)
├── deploy_to_server.sh        # Main deployment script (active)
├── docker-compose.yml         # Docker Compose config (required)
├── docker-compose.swarm.yml   # Swarm config (required)
├── Dockerfile                 # Docker build (required)
├── Makefile                   # Dev commands (optional)
├── intent_keywords_complete.sql # Keywords data (required)
├── docs/                      # All documentation
│   ├── AFFILIATE_IMPLEMENTATION_SUMMARY.md
│   ├── GITHUB_ACTION_FIX_SUMMARY.md
│   ├── MIGRATION_FIX_README.md
│   ├── PRODUCTION_FIX_GUIDE.md
│   └── ... (300+ other docs)
├── src/                       # Django application
├── monitoring/                # Prometheus/Grafana configs
├── email_template/           # Email assets
├── pilito-sync/              # WordPress plugin
└── fiko-woocommerce-sync/    # WooCommerce plugin
```

## Best Practices

### When to Add New Shell Scripts

Only add shell scripts to root if they are:
1. **Actively used** in deployment or CI/CD
2. **Docker-related** (entrypoints, health checks)
3. **General utilities** needed across the project

Otherwise, place them in:
- `docs/scripts/` - For documentation/examples
- `src/scripts/` - For application-specific scripts

### When to Add Documentation

All `.md` documentation files should go in:
- `docs/` - General documentation
- `docs/<category>/` - Category-specific docs
- `src/<app>/` - App-specific README files

## Deployment

For deployment, use:
```bash
./deploy_to_server.sh
```

This single script handles:
- Code deployment via rsync
- Database migrations
- Service restarts
- Health checks

## Development

For local development:
```bash
docker-compose up        # Start all services
make <command>          # Run common tasks
```

---

**Last Updated:** November 25, 2025
**Cleaned by:** Migration fix and organization

