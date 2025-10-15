# Node-Based Workflow System

## Overview

The enhanced workflow system now supports a visual, node-based approach that matches your Figma designs. This system provides four distinct node types that can be connected together to create sophisticated automation workflows.

## System Architecture

### Core Node Types

The system implements exactly 4 node types as specified:

#### 1. **When Node** (شروع‌کننده)
Entry points that define what triggers a workflow to start.

**Types:**
- **Receive Message** (`receive_message`): Triggered when a new message is received
- **Add Tag** (`add_tag`): Triggered when a tag is added to a customer
- **New Customer** (`new_customer`): Triggered when a new customer is created
- **Scheduled** (`scheduled`): Triggered at specific times/intervals

**Configuration Options:**
- **Keywords**: Array of keywords to match in messages
- **Tags**: Specific tags to monitor for
- **Channels**: Channels to monitor (`instagram`, `telegram`, `all`)
- **Schedule Settings**: Frequency, start date, and time for scheduled triggers

#### 2. **Condition Node** (شرط‌ها)
Logic gates that evaluate conditions before allowing workflow continuation.

**Combination Operators:**
- **AND**: All conditions must be true
- **OR**: At least one condition must be true (default)

**Condition Types:**
- **AI Condition**: Uses AI to evaluate custom prompts against message content
  - Field: `prompt` - The AI prompt to evaluate
- **Message Condition**: Evaluates message text with specific operators:
  - `equals_to` (=): Exact match
  - `not_equal` (≠): Not equal to value
  - `start_with`: Message starts with value
  - `end_with`: Message ends with value
  - `contains`: Message contains value

**JSON Structure:**
```json
{
  "combination_operator": "or",
  "conditions": [
    {
      "type": "ai",
      "prompt": "Is this message asking for help?"
    },
    {
      "type": "message",
      "operator": "contains",
      "value": "help"
    }
  ]
}
```

#### 3. **Action Node** (عملیات)
Executable actions that perform specific tasks.

**Action Types:**
- **Send Message** (`send_message`): Send text message to customer
- **Delay** (`delay`): Wait for specified time period
- **Redirect Conversation** (`redirect_conversation`): Transfer conversation to different department
- **Add Tag** (`add_tag`): Add tag to customer
- **Remove Tag** (`remove_tag`): Remove tag from customer
- **Transfer to Human** (`transfer_to_human`): Transfer conversation to human agent
- **Send Email** (`send_email`): Send email to customer
- **Webhook** (`webhook`): Call external webhook URL
- **Custom Code** (`custom_code`): Execute custom Python code

**Redirect Destinations:**
- `support`: Support Department
- `sales`: Sales Department
- `technical`: Technical Department
- `billing`: Billing Department
- `general`: General Department

**Delay Units:**
- `seconds`: Seconds
- `minutes`: Minutes (default)
- `hours`: Hours
- `days`: Days

**Webhook Methods:**
- `GET`, `POST` (default), `PUT`, `DELETE`
- **Redirect Conversation**: Route to support departments
  - Support, Sales, Technical, Billing, General
- **Add Tag** / **Remove Tag**: Manage customer tags
- **Transfer to Human**: Hand off to human operator
- **Webhook**: Call external APIs
- **Custom Code**: Execute custom Python code (sandboxed)

#### 4. **Waiting Node** (انتظار برای پاسخ کاربر)
Interactive nodes that wait for user responses before continuing.

**Answer Types:**
- **Text** (`text`): Any text input
- **Number** (`number`): Numeric input with validation
- **Email** (`email`): Email format validation
- **Phone** (`phone`): Phone number format validation
- **Date** (`date`): Date format validation
- **Choice Answer** (`choice`): Multiple choice from predefined options

**Storage Types:**
- **User Profile** (`user_profile`): Store in user profile data
- **Custom Field** (`custom_field`): Store in custom field
- **Database** (`database`): Store in database table
- **Session Storage** (`session`): Store in session data
- **Temporary Storage** (`temporary`): Temporary session-based storage

**Response Time Limit:**
- **Toggle Control**: Enable/disable response time limit
- **Delay Time**: Amount of time to wait
- **Time Unit**: seconds, minutes, hours, days

**Validation Features:**
- **Allowed Errors**: Number of retry attempts (default: 3)
- **Skip Keywords**: Words that skip this step
- **Exit Keywords**: Words that allow user to skip current step

**JSON Structure:**
```json
{
  "answer_type": "email",
  "storage_type": "user_profile", 
  "storage_field": "email",
  "customer_message": "Please enter your email address:",
  "response_time_limit_enabled": true,
  "response_timeout_amount": 30,
  "response_timeout_unit": "minutes",
  "allowed_errors": 3,
  "skip_keywords": ["skip", "pass", "next"]
}
```

## API Endpoints

### Node-Based Workflow Management

#### Workflows with Nodes
```
GET    /api/v1/workflow/api/node-workflows/           # List workflows with node structure
POST   /api/v1/workflow/api/node-workflows/           # Create new workflow
GET    /api/v1/workflow/api/node-workflows/{id}/      # Get workflow details with nodes
PUT    /api/v1/workflow/api/node-workflows/{id}/      # Update workflow
DELETE /api/v1/workflow/api/node-workflows/{id}/      # Delete workflow
```

#### Node Management
```
GET    /api/v1/workflow/api/node-workflows/{id}/nodes/         # Get all nodes
POST   /api/v1/workflow/api/node-workflows/{id}/create_node/   # Create new node
GET    /api/v1/workflow/api/node-workflows/{id}/connections/   # Get all connections
POST   /api/v1/workflow/api/node-workflows/{id}/create_connection/ # Create connection
```

#### Individual Node Types
```
GET    /api/v1/workflow/api/when-nodes/              # When nodes
GET    /api/v1/workflow/api/condition-nodes/         # Condition nodes  
GET    /api/v1/workflow/api/action-nodes/            # Action nodes
GET    /api/v1/workflow/api/waiting-nodes/           # Waiting nodes
```

#### Execution
```
POST   /api/v1/workflow/api/node-workflows/{id}/execute_with_nodes/  # Execute workflow
GET    /api/v1/workflow/api/user-responses/          # User responses to waiting nodes
```

## Usage Examples

### Example 1: Customer Support Routing

Create a workflow that routes customers based on their inquiry:

1. **When Node**: Receive Message (keywords: ["پشتیبانی", "مشکل", "کمک"])
2. **Condition Node**: AI Condition ("آیا این پیام مربوط به مشکل فنی است؟")
3. **Action Node**: Redirect Conversation → Technical Support
4. **Action Node**: Send Message ("پیام شما به تیم فنی ارجاع داده شد")

### Example 2: Lead Qualification

Interactive lead qualification process:

1. **When Node**: New Customer
2. **Action Node**: Send Message ("سلام! خوش آمدید. لطفاً نام خود را وارد کنید:")
3. **Waiting Node**: Text input → Store in customer.first_name
4. **Action Node**: Send Message ("چه محصولی شما را علاقه‌مند کرده؟")
5. **Waiting Node**: Choice options → ["لپ‌تاپ", "موبایل", "لوازم جانبی"]
6. **Condition Node**: Check choice
7. **Action Node**: Add appropriate tag based on interest

### Example 3: Scheduled Follow-up

Automated follow-up for inactive customers:

1. **When Node**: Scheduled (Daily at 10:00 AM)
2. **Condition Node**: User last activity > 7 days
3. **Action Node**: Send Message ("شما را دلتان کرده‌ایم! تخفیف ویژه برای بازگشت شما")
4. **Action Node**: Add Tag "follow_up_sent"

## Database Schema

### Core Models

```python
# Base node model
WorkflowNode(
    workflow: ForeignKey,
    node_type: CharField,  # 'when', 'condition', 'action', 'waiting'
    title: CharField,
    position_x: FloatField,
    position_y: FloatField,
    configuration: JSONField,
    is_active: BooleanField
)

# Specific node types inherit from WorkflowNode
WhenNode(WorkflowNode)
ConditionNode(WorkflowNode)  
ActionNode(WorkflowNode)
WaitingNode(WorkflowNode)

# Connections between nodes
NodeConnection(
    workflow: ForeignKey,
    source_node: ForeignKey,
    target_node: ForeignKey,
    connection_type: CharField,  # 'success', 'failure', 'timeout', 'skip'
    condition: JSONField
)

# User responses to waiting nodes
UserResponse(
    waiting_node: ForeignKey,
    workflow_execution: ForeignKey,
    user_id: CharField,
    response_value: TextField,
    is_valid: BooleanField,
    error_count: PositiveIntegerField
)
```

## Creating Nodes via API

### Create When Node
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "when",
    "title": "پیام دریافت شد",
    "when_type": "receive_message",
    "keywords": ["سلام", "کمک"],
    "channels": ["telegram", "instagram"],
    "position_x": 100,
    "position_y": 200
}
```

### Create Condition Node
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "condition",
    "title": "بررسی علاقه به محصول",
    "combination_operator": "or",
    "conditions": [
        {
            "type": "ai",
            "prompt": "آیا کاربر علاقه به خرید محصول نشان داده؟"
        },
        {
            "type": "message",
            "operator": "contains",
            "value": "خرید"
        },
        {
            "type": "message", 
            "operator": "start_with",
            "value": "سلام"
        }
    ]
}
```

### Get Condition Configuration Options
```bash
# Get condition types
GET /api/v1/workflow/api/condition-nodes/condition_types/

# Get message operators  
GET /api/v1/workflow/api/condition-nodes/message_operators/

# Get combination operators
GET /api/v1/workflow/api/condition-nodes/combination_operators/
```

### Test Condition Node
```json
POST /api/v1/workflow/api/condition-nodes/{node_id}/test/
{
    "context": {
        "event": {
            "data": {
                "content": "سلام، می‌خواهم محصول بخرم"
            }
        },
        "user": {
            "first_name": "احمد"
        }
    }
}
```

### Create Action Node

#### Send Message Action
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "action",
    "title": "ارسال پیام خوشامد",
    "action_type": "send_message",
    "message_content": "سلام {{user.first_name}}! به فروشگاه ما خوش آمدید."
}
```

#### Delay Action
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "action",
    "title": "انتظار 5 دقیقه",
    "action_type": "delay",
    "delay_amount": 5,
    "delay_unit": "minutes"
}
```

#### Add Tag Action
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "action",
    "title": "اضافه کردن تگ VIP",
    "action_type": "add_tag",
    "tag_name": "VIP"
}
```

#### Redirect Conversation Action
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "action",
    "title": "انتقال به پشتیبانی",
    "action_type": "redirect_conversation",
    "redirect_destination": "support"
}
```

#### Webhook Action
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "action",
    "title": "فراخوانی API خارجی",
    "action_type": "webhook",
    "webhook_url": "https://api.example.com/notify",
    "webhook_method": "POST",
    "webhook_headers": {"Authorization": "Bearer token"},
    "webhook_payload": {"customer_id": "{{user.id}}", "event": "workflow_triggered"}
}
```

#### Custom Code Action
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "action",
    "title": "محاسبه امتیاز",
    "action_type": "custom_code",
    "custom_code": "# Calculate customer score\nuser_score = context.get('user', {}).get('total_orders', 0) * 10\ncontext['user']['score'] = user_score"
}
```

### Create Waiting Node

#### Text Answer Example
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "waiting",
    "title": "درخواست نام",
    "answer_type": "text",
    "storage_type": "user_profile",
    "storage_field": "first_name",
    "customer_message": "لطفاً نام خود را وارد کنید:",
    "response_time_limit_enabled": true,
    "response_timeout_amount": 30,
    "response_timeout_unit": "minutes",
    "allowed_errors": 3,
    "skip_keywords": ["skip", "pass"]
}
```

#### Email Answer with Database Storage
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "waiting",
    "title": "درخواست ایمیل",
    "answer_type": "email",
    "storage_type": "database",
    "storage_field": "email_address",
    "customer_message": "لطفاً آدرس ایمیل خود را وارد کنید:",
    "response_time_limit_enabled": true,
    "response_timeout_amount": 5,
    "response_timeout_unit": "minutes",
    "allowed_errors": 2,
    "skip_keywords": ["skip"]
}
```

#### Choice Answer Example
```json
POST /api/v1/workflow/api/node-workflows/123/create_node/
{
    "node_type": "waiting",
    "title": "انتخاب سطح پشتیبانی",
    "answer_type": "choice",
    "storage_type": "session",
    "storage_field": "support_level",
    "customer_message": "لطفاً نوع پشتیبانی مورد نیاز خود را انتخاب کنید:",
    "choice_options": ["فنی", "فروش", "حسابداری", "عمومی"],
    "response_time_limit_enabled": false,
    "allowed_errors": 3
}
```

### Get Waiting Node Configuration Options

#### Get Answer Types
```bash
GET /api/v1/workflow/api/waiting-nodes/answer_types/
```

#### Get Storage Types  
```bash
GET /api/v1/workflow/api/waiting-nodes/storage_types/
```

#### Get Time Units
```bash
GET /api/v1/workflow/api/waiting-nodes/time_units/
```

### Create Node Connection
```json
POST /api/v1/workflow/api/node-workflows/123/create_connection/
{
    "source_node_id": "uuid-of-source-node",
    "target_node_id": "uuid-of-target-node", 
    "connection_type": "success"
}
```

## AI Integration

### AI Condition Evaluation

The system integrates with your existing AI service to evaluate conditions:

```python
# Example AI condition
{
    "type": "ai",
    "ai_prompt": "آیا این پیام شامل درخواست تخفیف است؟"
}
```

The AI service receives a prompt in Persian and returns `true` or `false` based on message analysis.

## Template Variables

All text fields support template variables:

- `{{user.first_name}}` - Customer's first name
- `{{user.email}}` - Customer's email  
- `{{user.source}}` - Channel (instagram/telegram)
- `{{event.data.content}}` - Original message content
- `{{event.timestamp}}` - Event timestamp
- `{{user_response_node_id}}` - Previous user responses

## Admin Interface

Complete admin interface for managing:

- **WorkflowNode**: Base node management
- **WhenNode**: Trigger configuration
- **ConditionNode**: Condition logic setup
- **ActionNode**: Action configuration  
- **WaitingNode**: User interaction setup
- **NodeConnection**: Flow connections
- **UserResponse**: Response monitoring

## Migration & Deployment

### Run Migration
```bash
cd src
source ../venv/bin/activate
python manage.py migrate workflow
```

### API Testing
```bash
# Create a test workflow
curl -X POST http://localhost:8000/api/v1/workflow/api/node-workflows/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "تست فلوچارت",
    "description": "فلوچارت تست برای سیستم جدید",
    "status": "DRAFT"
  }'
```

## Benefits of Node-Based System

1. **Visual Design Ready**: Matches Figma designs perfectly
2. **Modular & Reusable**: Nodes can be reused across workflows
3. **Interactive Workflows**: Waiting nodes enable two-way communication
4. **AI-Powered Decisions**: AI conditions for intelligent routing
5. **Flexible Connections**: Multiple connection types (success/failure/timeout)
6. **Complete API**: Full REST API for frontend integration
7. **Admin Friendly**: Comprehensive admin interface
8. **Scalable**: Designed for complex multi-step workflows

## Next Steps

1. **Frontend Integration**: Connect to visual workflow builder
2. **Advanced Scheduling**: Celery integration for time-based triggers  
3. **Analytics Dashboard**: Workflow performance metrics
4. **Template Library**: Pre-built workflow templates
5. **A/B Testing**: Workflow variant testing capabilities

---

**The enhanced workflow system provides a powerful, visual, and intuitive way to create sophisticated customer automation flows that integrate seamlessly with your existing platform.**
