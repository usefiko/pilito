#!/bin/bash
# Deploy fixed migrations by copying files directly to server

set -e

SERVER="root@185.164.72.165"
PASSWORD="9188945776poST?"
PROJECT_DIR="/root/pilito"

echo "🚀 Deploying fixed migrations to production server..."

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass is not installed. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass
    else
        echo "Please install sshpass manually"
        exit 1
    fi
fi

echo "📁 Step 1: Copying fixed migration files to server..."

# Copy accounts migration
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no \
    "/Users/nima/Projects/pilito/src/accounts/migrations/0013_user_email_confirmed_user_invite_code_and_more.py" \
    "${SERVER}:${PROJECT_DIR}/src/accounts/migrations/"

echo "✅ Copied accounts migration 0013"

# Copy integrations migration
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no \
    "/Users/nima/Projects/pilito/src/integrations/migrations/0002_wordpresscontent_wordpresscontenteventlog_and_more.py" \
    "${SERVER}:${PROJECT_DIR}/src/integrations/migrations/"

echo "✅ Copied integrations migration 0002"

# Copy settings migration
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no \
    "/Users/nima/Projects/pilito/src/settings/migrations/0016_intercomtickettype_alter_generalsettings_options_and_more.py" \
    "${SERVER}:${PROJECT_DIR}/src/settings/migrations/"

echo "✅ Copied settings migration 0016"

echo ""
echo "🔄 Step 2: Restarting containers and running migrations..."

# SSH and restart
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" << 'ENDSSH'
set -e

cd /root/pilito

echo "🛑 Stopping containers..."
docker-compose down

echo ""
echo "🔨 Rebuilding containers..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
docker-compose build --parallel

echo ""
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 30

echo ""
echo "🔍 Checking Django app..."
if docker ps | grep -q django_app; then
    echo "✅ Django app container is running"
    
    echo ""
    echo "📊 Running migrations with safe migrations..."
    docker exec django_app python manage.py migrate --noinput
    
    echo ""
    echo "✅ Migrations completed successfully!"
    
    echo ""
    echo "📊 Verifying migration status..."
    echo "Accounts migrations:"
    docker exec django_app python manage.py showmigrations accounts | tail -5
    echo ""
    echo "Integrations migrations:"
    docker exec django_app python manage.py showmigrations integrations | tail -5
    
    echo ""
    echo "🔍 Running Django check..."
    docker exec django_app python manage.py check
    
    echo ""
    echo "✅ All checks passed!"
else
    echo "❌ Django app container failed to start"
    echo ""
    echo "📋 Container logs:"
    docker logs django_app --tail 100
    exit 1
fi

echo ""
echo "📊 Final container status:"
docker-compose ps

echo ""
echo "✅ Deployment completed successfully!"
ENDSSH

echo ""
echo "🎉 Production deployment successful!"
echo ""
echo "✅ Fixed migrations deployed:"
echo "  - accounts.0013 (safe)"
echo "  - integrations.0002 (safe)"
echo "  - settings.0016 (safe)"
echo ""
echo "🔍 Verification steps:"
echo "1. Check application: https://api.pilito.com/health/"
echo "2. Check logs: docker logs django_app --tail 50"
echo "3. Check services: docker-compose ps"

