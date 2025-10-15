# Fiko Backend Documentation

Welcome to the Fiko Backend documentation! This directory contains comprehensive documentation for all aspects of the Fiko platform.

## 📁 Documentation Structure

### 🤖 [AI Features](./ai-features/)
AI-powered features, RAG implementation, prompt generation, and intelligence systems:
- AI usage tracking and monitoring
- Contact escalation
- Intent detection and routing
- Session memory and context
- Prompt generation system
- RAG (Retrieval-Augmented Generation) pipeline
- Persona and tone customization
- Performance optimization

### 🚀 [Deployment](./deployment/)
Production deployment guides, infrastructure setup, and configuration:
- AWS instance sizing and setup
- Deployment checklists and instructions
- Production diagnostics
- Production fixes and updates
- Stripe deployment migration

### 🗄️ [Database](./database/)
Database configuration, migrations, and optimizations:
- Database connection fixes
- PostgreSQL collation configuration
- PgVector migration guides
- Embedding dimensions setup

### 📊 [Monitoring](./monitoring/)
System monitoring, metrics, and health checks:
- Prometheus and Grafana setup
- Monitoring implementation
- Disk management
- Quick start guides

### 💳 [Stripe & Billing](./stripe-billing/)
Payment processing, subscription management, and billing:
- Stripe integration guides
- Webhook setup
- Subscription management
- Billing UX guidelines
- Cancellation and deactivation flows

### 🔧 [Fixes & Troubleshooting](./fixes/)
Bug fixes, patches, and issue resolutions:
- Webhook fixes
- Google OAuth fixes
- QA system debugging
- Various system fixes

### 🧪 [Testing](./testing/)
Testing guides, test suites, and quality assurance:
- API testing guides
- Feature testing instructions
- RAG status testing
- OAuth testing
- Product extraction testing

### 📋 [Workflows](./workflows/)
Workflow system documentation:
- Workflow chat integration
- Export/import functionality
- Monitoring guides
- System testing

### 🔐 [Authentication](./authentication/)
Authentication and authorization systems:
- Google OAuth implementation
- User isolation
- Email confirmation
- JWT implementation

### 🛠️ [Scripts](./scripts/)
Utility scripts, helpers, and automation tools:
- Database migration scripts
- Monitoring scripts
- Testing scripts
- Deployment automation
- Health check scripts

---

## 📖 Core Documentation

### Quick Start Guides
- [Setup Complete Guide](./SETUP_COMPLETE_GUIDE.md)
- [Quick Start - New APIs](./QUICK_START_NEW_APIS.md)
- [API Quick Reference](./API_QUICK_REFERENCE.md)

### Implementation Summaries
- [Implementation Complete](./IMPLEMENTATION_COMPLETE.md)
- [Phase 1 Implementation](./PHASE1_IMPLEMENTATION_SUMMARY.md)
- [Phase 2 Roadmap](./PHASE2_ROADMAP.md)
- [Changes Summary](./CHANGES_SUMMARY.md)

### API Documentation
- [API Update Summary](./API_UPDATE_SUMMARY.md)
- [API Usage Examples](./API_USAGE_EXAMPLES.md)
- [Web Knowledge API Updates](./WEB_KNOWLEDGE_API_UPDATES.md)
- [Marketing Workflow API Reference](./MARKETING_WORKFLOW_API_REFERENCE.md)
- [Product Management API](./PRODUCT_MANAGEMENT_API.md)
- [WebSocket API Documentation](./WEBSOCKET_API_DOCUMENTATION.md)

### Architecture & Design
- [AI Model Documentation](./AI_MODEL_DOCUMENTATION.md)
- [Web Knowledge Architecture](./WEB_KNOWLEDGE_ARCHITECTURE.md)
- [Node-Based Workflow System](./NODE_BASED_WORKFLOW_SYSTEM.md)

### Configuration Files
- [Stripe Environment Variables](./STRIPE_ENVIRONMENT_VARIABLES.txt)
- [Intent Keywords Example](./INTENT_KEYWORDS_EXAMPLE_OUTPUT.json)
- [Intent Routing Example](./INTENT_ROUTING_EXAMPLE_OUTPUT.json)

---

## 🔍 Finding Documentation

### By Feature
- **AI Features**: See [ai-features/](./ai-features/)
- **Billing**: See [stripe-billing/](./stripe-billing/)
- **Workflows**: See [workflows/](./workflows/)
- **Authentication**: See [authentication/](./authentication/)

### By Activity
- **Setting up**: Check [deployment/](./deployment/) and `SETUP_COMPLETE_GUIDE.md`
- **Troubleshooting**: Check [fixes/](./fixes/) and `DEPLOYMENT_TROUBLESHOOTING.md`
- **Testing**: Check [testing/](./testing/) and [scripts/](./scripts/)
- **Monitoring**: Check [monitoring/](./monitoring/)

### By API
- **Customer APIs**: `CUSTOMER_BULK_APIS.md`, `CUSTOMER_WEBSOCKET_*.md`
- **Workflow APIs**: [workflows/](./workflows/), `MARKETING_WORKFLOW_API_REFERENCE.md`
- **Web Knowledge**: `WEB_KNOWLEDGE_*.md`, `WEBKNOWLEDGE_*.md`
- **QA System**: `QA_GENERATION_*.md`, `ENHANCED_QA_SYSTEM.md`

---

## 🆕 Latest Updates

### AI Usage Tracking (October 2025)
- Comprehensive AI usage tracking system
- Real-time monitoring with detailed logging
- Production diagnostic tools
- See [ai-features/AI_USAGE_TRACKING_*.md](./ai-features/)

### Production Fixes (October 2025)
- Database collation fixes
- OAuth improvements
- WebSocket optimizations
- See [deployment/PRODUCTION_FIXES_OCT_2025.md](./deployment/)

---

## 🛟 Need Help?

1. **Quick Reference**: Start with `API_QUICK_REFERENCE.md`
2. **Setup Issues**: Check [deployment/](./deployment/) and [fixes/](./fixes/)
3. **API Questions**: See [API_USAGE_EXAMPLES.md](./API_USAGE_EXAMPLES.md)
4. **Testing**: Check [testing/](./testing/) and [scripts/](./scripts/)
5. **Scripts**: All utility scripts are in [scripts/](./scripts/)

---

**Last Updated:** October 11, 2025  
**Version:** 1.0
