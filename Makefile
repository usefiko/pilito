# Pilito Docker Swarm Management Makefile
# =========================================
# Simplifies common Docker Swarm operations

.PHONY: help init deploy update scale status health logs clean rollback monitor

# Default target
.DEFAULT_GOAL := help

# Stack name
STACK_NAME := pilito

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

help: ## Show this help message
	@echo "$(BLUE)Pilito Docker Swarm Management$(NC)"
	@echo "==============================="
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  1. make init     # Initialize swarm (first time only)"
	@echo "  2. make deploy   # Deploy the stack"
	@echo "  3. make status   # Check status"
	@echo "  4. make health   # Run health checks"

init: ## Initialize Docker Swarm cluster
	@echo "$(GREEN)Initializing Docker Swarm...$(NC)"
	@./swarm_init.sh

deploy: ## Deploy the stack to Docker Swarm
	@echo "$(GREEN)Deploying stack...$(NC)"
	@./swarm_deploy.sh

update: ## Update all services with zero downtime
	@echo "$(GREEN)Updating services...$(NC)"
	@./swarm_update.sh

scale: ## Scale a service (usage: make scale service=web replicas=5)
	@if [ -z "$(service)" ] || [ -z "$(replicas)" ]; then \
		echo "$(YELLOW)Usage: make scale service=<name> replicas=<count>$(NC)"; \
		echo "Example: make scale service=web replicas=5"; \
	else \
		echo "$(GREEN)Scaling $(service) to $(replicas) replicas...$(NC)"; \
		./swarm_scale.sh $(service) $(replicas); \
	fi

rollback: ## Rollback a service (usage: make rollback service=web)
	@if [ -z "$(service)" ]; then \
		echo "$(YELLOW)Usage: make rollback service=<name>$(NC)"; \
		echo "Example: make rollback service=web"; \
	else \
		echo "$(GREEN)Rolling back $(service)...$(NC)"; \
		./swarm_rollback.sh $(service); \
	fi

status: ## Show comprehensive status of the cluster
	@./swarm_status.sh

health: ## Run health checks on all services
	@./health_check_services.sh

monitor: ## Start continuous monitoring dashboard
	@./continuous_monitoring.sh

logs: ## View service logs (usage: make logs service=web)
	@if [ -z "$(service)" ]; then \
		echo "$(YELLOW)Usage: make logs service=<name>$(NC)"; \
		echo "Example: make logs service=web"; \
		echo ""; \
		echo "Available services:"; \
		docker stack services $(STACK_NAME) --format "  - {{.Name}}" 2>/dev/null | sed 's/$(STACK_NAME)_//'; \
	else \
		docker service logs -f $(STACK_NAME)_$(service); \
	fi

ps: ## Show all running tasks
	@docker stack ps $(STACK_NAME)

services: ## List all services
	@docker stack services $(STACK_NAME)

nodes: ## Show all swarm nodes
	@docker node ls

clean: ## Remove the stack (keeps data)
	@echo "$(YELLOW)Removing stack (data will be preserved)...$(NC)"
	@docker stack rm $(STACK_NAME)
	@echo "$(GREEN)Stack removed. Waiting for cleanup...$(NC)"
	@sleep 10

clean-full: ## Remove stack and all data (DESTRUCTIVE!)
	@echo "$(YELLOW)⚠️  WARNING: This will delete all data!$(NC)"
	@./swarm_cleanup.sh

# Docker Compose (for local development)
dev-up: ## Start local development environment
	@echo "$(GREEN)Starting development environment...$(NC)"
	@docker-compose up -d

dev-down: ## Stop local development environment
	@echo "$(GREEN)Stopping development environment...$(NC)"
	@docker-compose down

dev-logs: ## View development logs
	@docker-compose logs -f

# Utility targets
build: ## Build Docker images
	@echo "$(GREEN)Building images...$(NC)"
	@docker-compose -f docker-compose.swarm.yml build

shell: ## Open shell in web service container
	@docker exec -it $$(docker ps -q -f "name=$(STACK_NAME)_web" | head -n 1) /bin/bash

db-shell: ## Open PostgreSQL shell
	@docker exec -it $$(docker ps -q -f "name=$(STACK_NAME)_db" | head -n 1) psql -U postgres pilito_db

redis-cli: ## Open Redis CLI
	@docker exec -it $$(docker ps -q -f "name=$(STACK_NAME)_redis" | head -n 1) redis-cli

# Backup and restore
backup-db: ## Backup PostgreSQL database
	@echo "$(GREEN)Backing up database...$(NC)"
	@mkdir -p backups
	@docker exec $$(docker ps -q -f "name=$(STACK_NAME)_db" | head -n 1) \
		pg_dump -U postgres pilito_db > backups/db_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Database backup completed$(NC)"

backup-media: ## Backup media files
	@echo "$(GREEN)Backing up media files...$(NC)"
	@mkdir -p backups
	@docker run --rm -v $(STACK_NAME)_media_volume:/data -v $$(pwd)/backups:/backup \
		alpine tar czf /backup/media_backup_$$(date +%Y%m%d_%H%M%S).tar.gz /data
	@echo "$(GREEN)Media backup completed$(NC)"

# Quick actions
restart: ## Quick restart of web service
	@docker service update --force $(STACK_NAME)_web

restart-celery: ## Quick restart of celery workers
	@docker service update --force $(STACK_NAME)_celery_worker

# Information
info: ## Show cluster information
	@echo "$(BLUE)Docker Swarm Information$(NC)"
	@echo "========================"
	@docker info | grep -A 10 "Swarm:"

version: ## Show Docker version
	@docker version

# Migration helpers
migrate: ## Run Django migrations
	@docker exec $$(docker ps -q -f "name=$(STACK_NAME)_web" | head -n 1) \
		python manage.py migrate

collectstatic: ## Collect static files
	@docker exec $$(docker ps -q -f "name=$(STACK_NAME)_web" | head -n 1) \
		python manage.py collectstatic --noinput

createsuperuser: ## Create Django superuser
	@docker exec -it $$(docker ps -q -f "name=$(STACK_NAME)_web" | head -n 1) \
		python manage.py createsuperuser

# Testing
test-health: ## Test health endpoints
	@echo "$(GREEN)Testing health endpoints...$(NC)"
	@echo -n "Web Service:    "
	@curl -sf http://localhost:8000/health/ > /dev/null && echo "$(GREEN)✓$(NC)" || echo "$(YELLOW)✗$(NC)"
	@echo -n "Prometheus:     "
	@curl -sf http://localhost:9090/-/healthy > /dev/null && echo "$(GREEN)✓$(NC)" || echo "$(YELLOW)✗$(NC)"
	@echo -n "Grafana:        "
	@curl -sf http://localhost:3001/api/health > /dev/null && echo "$(GREEN)✓$(NC)" || echo "$(YELLOW)✗$(NC)"

# Documentation
docs: ## Open documentation in browser
	@echo "$(GREEN)Opening documentation...$(NC)"
	@if command -v xdg-open > /dev/null; then \
		xdg-open DOCKER_SWARM_GUIDE.md; \
	elif command -v open > /dev/null; then \
		open DOCKER_SWARM_GUIDE.md; \
	else \
		echo "Please open DOCKER_SWARM_GUIDE.md manually"; \
	fi

quickstart: ## Open quick start guide
	@if command -v xdg-open > /dev/null; then \
		xdg-open SWARM_QUICKSTART.md; \
	elif command -v open > /dev/null; then \
		open SWARM_QUICKSTART.md; \
	else \
		echo "Please open SWARM_QUICKSTART.md manually"; \
	fi

