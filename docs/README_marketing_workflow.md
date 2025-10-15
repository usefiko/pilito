# Marketing Workflow Module

A comprehensive event-driven, rule-based automation system for the Fiko platform that enables sophisticated marketing workflows triggered by user interactions.

## 🚀 Features

- **Event-Driven Architecture**: Automatically responds to user messages, registrations, and other events
- **Rule-Based Automation**: Complex condition evaluation with AND/OR logic and custom code support
- **Multi-Channel Support**: Send messages via Telegram, Instagram, and email
- **Visual Workflow Builder Ready**: Models designed for future frontend integration with Figma designs
- **Comprehensive API**: Full REST API for workflow management
- **Admin Interface**: Django admin integration for easy management
- **Fallback Integration**: Seamlessly integrates with existing AI response system
- **Audit Trail**: Complete logging and execution tracking

## 📋 System Requirements

- Django 5+
- PostgreSQL
- Redis (for Celery)
- Celery worker processes

## 🛠️ Installation & Setup

### 1. The workflow app is already integrated into the project
The marketing workflow system has been implemented in the existing `workflow` Django app with full backward compatibility.

### 2. Run Migrations
```bash
cd src/
python manage.py migrate workflow
```

### 3. Initialize Workflow System
```bash
python manage.py init_workflow_system
```

### 4. Set Up Sample Data (Optional)
```bash
python manage.py setup_sample_workflows
```

### 5. Environment Variables
Add these optional environment variables for external integrations:

```bash
# Optional: For Telegram message sending
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional: For Instagram message sending via N8N
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/instagram

# Optional: For email sending
DEFAULT_FROM_EMAIL=noreply@fiko.net
```

## 🏗️ Architecture

### Core Models

1. **EventType**: Defines types of events (MESSAGE_RECEIVED, USER_CREATED, etc.)
2. **Trigger**: Defines what events trigger workflows and conditions
3. **Condition**: Logical rule evaluation with support for complex conditions
4. **Action**: Individual actions to execute (send_message, add_tag, webhook, etc.)
5. **Workflow**: Combines triggers, conditions, and actions into automation flows
6. **WorkflowExecution**: Tracks individual workflow runs with full audit trail

### Key Components

- **Condition Evaluator**: Secure rule evaluation engine with custom code sandbox
- **Trigger Service**: Event processing and workflow discovery
- **Workflow Execution Service**: Action execution with error handling and retries
- **Settings Adapters**: Maps existing project models to workflow canonical names

## 🔗 API Endpoints

All endpoints are available under `/api/v1/workflow/api/`:

### Workflows
- `GET /workflows/` - List workflows
- `POST /workflows/` - Create workflow  
- `GET /workflows/{id}/` - Get workflow details
- `PUT /workflows/{id}/` - Update workflow
- `DELETE /workflows/{id}/` - Delete workflow
- `POST /workflows/{id}/activate/` - Activate workflow
- `POST /workflows/{id}/pause/` - Pause workflow
- `POST /workflows/{id}/execute/` - Manually execute workflow

### Triggers
- `GET /triggers/` - List triggers
- `POST /triggers/` - Create trigger
- `POST /triggers/process_event/` - Process event and trigger workflows
- `POST /triggers/{id}/test/` - Test trigger with sample data

### Actions
- `GET /actions/` - List actions
- `POST /actions/` - Create action
- `GET /actions/action_types/` - Get available action types
- `POST /actions/{id}/test/` - Test action execution

### Monitoring
- `GET /workflow-executions/` - List workflow executions
- `GET /trigger-event-logs/` - List trigger events
- `GET /workflows/statistics/` - Get workflow statistics

## 🎯 Usage Examples

### Example 1: Coupon Request Workflow

This workflow automatically sends discount codes when customers ask for coupons:

**Trigger**: Message contains "کد تخفیف", "coupon", or "discount"  
**Condition**: User has "interested" tag  
**Actions**:
1. Send personalized coupon message
2. Add "coupon_sent" tag
3. Wait 10 minutes
4. Send follow-up email

### Example 2: Welcome New Users

**Trigger**: New customer registration  
**Actions**:
1. Send welcome message in Persian
2. Add "welcomed" tag

### Testing via API

```bash
# Test event processing
curl -X POST http://localhost:8000/api/v1/workflow/api/triggers/process_event/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "event_type": "MESSAGE_RECEIVED",
    "data": {
      "message_id": "msg123",
      "content": "سلام، کد تخفیف دارید؟",
      "timestamp": "2024-01-01T10:00:00Z"
    },
    "user_id": "customer123",
    "conversation_id": "conv123"
  }'
```

## 🔧 Action Types

### Available Actions

1. **send_message**: Send message to customer via their channel (Telegram/Instagram)
2. **send_email**: Send email to customer
3. **add_tag**: Add tag to customer
4. **remove_tag**: Remove tag from customer
5. **update_user**: Update customer fields
6. **add_note**: Add internal note to conversation
7. **webhook**: Call external webhook
8. **wait**: Delay execution
9. **set_conversation_status**: Change conversation status
10. **custom_code**: Execute custom Python code (sandboxed)

### Template Variables

Actions support template variables using `{{path.to.value}}` syntax:

- `{{user.first_name}}` - Customer's first name
- `{{user.email}}` - Customer's email
- `{{event.data.content}}` - Message content
- `{{event.timestamp}}` - Event timestamp

## 🔍 Condition Operators

- **equals/not_equals**: Exact match
- **contains/icontains**: String contains (case-sensitive/insensitive)
- **starts_with/ends_with**: String prefix/suffix
- **in/not_in**: Value in list
- **is_null/is_not_null**: Null checks
- **is_empty/is_not_empty**: Empty checks
- **greater/less**: Numeric comparisons
- **between/not_between**: Range checks
- **matches_regex**: Regular expression matching

## 🧠 AI Fallback Integration

When no workflows are triggered for a `MESSAGE_RECEIVED` event on an active conversation, the system automatically calls the existing AI response task (`AI_model.tasks.process_ai_response_async`).

This ensures seamless integration with existing AI functionality while adding workflow automation capabilities.

## 📊 Monitoring & Logging

### Admin Interface
- Access via Django admin at `/admin/`
- Full workflow management interface
- Execution monitoring and debugging
- Event log viewing

### Audit Trail
- All workflow executions are logged
- Action-level execution tracking
- Error messages and retry attempts
- Performance metrics

### Celery Tasks
- `process_event`: Process trigger events
- `execute_workflow_action`: Execute individual actions
- `cleanup_old_executions`: Periodic cleanup
- `retry_failed_actions`: Retry failed actions

## 🔒 Security Features

- **Sandboxed Code Execution**: Custom code runs in restricted environment
- **Input Validation**: All API inputs are validated
- **Rate Limiting**: Workflow execution limits per user
- **Secret Redaction**: Sensitive data redacted from logs
- **Permission Checks**: Admin access required for management

## 📈 Performance Considerations

- **Async Processing**: All workflows execute asynchronously via Celery
- **Database Indexing**: Optimized queries with proper indexes
- **Pagination**: API responses are paginated
- **Cleanup Tasks**: Automatic cleanup of old execution data

## 🐛 Troubleshooting

### Common Issues

1. **Workflows not triggering**
   - Check trigger is active (`is_active=True`)
   - Verify trigger filters match event data
   - Check workflow status is `ACTIVE`

2. **Actions failing**
   - Check action configuration
   - Verify external service credentials (Telegram, email)
   - Review error logs in admin

3. **Performance issues**
   - Monitor Celery queue length
   - Check database query performance
   - Review workflow complexity

### Debug Mode
Enable debug logging in Django settings:
```python
LOGGING = {
    'loggers': {
        'workflow': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}
```

## 🔮 Future Enhancements

- Visual workflow builder frontend (Figma designs ready)
- Advanced scheduling options
- Workflow templates marketplace
- A/B testing capabilities
- Advanced analytics and reporting
- Integration with more channels (WhatsApp, SMS)

## 📚 Developer Resources

- **Models**: `src/workflow/models.py`
- **API Views**: `src/workflow/api/views.py`
- **Services**: `src/workflow/services/`
- **Tests**: `src/workflow/tests/`
- **Admin**: `src/workflow/admin.py`

## 🤝 Contributing

When extending the workflow system:

1. Follow existing patterns in the codebase
2. Add comprehensive tests for new features
3. Update documentation
4. Ensure backward compatibility
5. Test with existing AI integration

---

**Built with ❤️ for the Fiko platform**

The Marketing Workflow Module provides powerful automation capabilities while maintaining simplicity and reliability. It's designed to scale with your business needs and integrate seamlessly with existing platform features.
