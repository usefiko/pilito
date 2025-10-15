## 🌐 Marketing Workflow APIs Quick Reference

### Base URL: `http://localhost:8000/api/v1/workflow/api/`

| Category | Endpoint | Method | Description |
|----------|----------|---------|-------------|
| **Workflows** | `/workflows/` | GET | List all workflows |
| | `/workflows/` | POST | Create new workflow |
| | `/workflows/{id}/` | GET | Get workflow details |
| | `/workflows/{id}/` | PUT/PATCH | Update workflow |
| | `/workflows/{id}/` | DELETE | Delete workflow |
| | `/workflows/{id}/activate/` | POST | Activate workflow |
| | `/workflows/{id}/pause/` | POST | Pause workflow |
| | `/workflows/{id}/execute/` | POST | Execute workflow manually |
| | `/workflows/statistics/` | GET | Get workflow statistics |
| **Triggers** | `/triggers/` | GET | List all triggers |
| | `/triggers/` | POST | Create new trigger |
| | `/triggers/{id}/test/` | POST | Test trigger conditions |
| | `/triggers/process_event/` | POST | **Main event processing** |
| **Actions** | `/actions/` | GET | List all actions |
| | `/actions/` | POST | Create new action |
| | `/actions/action_types/` | GET | Get available action types |
| | `/actions/{id}/test/` | POST | Test action execution |
| **Monitoring** | `/workflow-executions/` | GET | List workflow executions |
| | `/trigger-event-logs/` | GET | List trigger events |
| | `/action-logs/` | GET | List action logs |

### 🔥 Most Important Endpoints:

1. **Process Events**: `POST /triggers/process_event/` - Main automation trigger
2. **List Workflows**: `GET /workflows/` - Get all workflows  
3. **Activate Workflow**: `POST /workflows/{id}/activate/` - Enable automation
4. **Monitor Executions**: `GET /workflow-executions/` - Track performance

### 📖 Complete documentation: `docs/MARKETING_WORKFLOW_API_REFERENCE.md`
