# Waiting Node API - Complete Examples

This document provides complete examples for creating and managing Waiting nodes, with proper field mapping between frontend and backend.

## 📋 Field Mapping

### Frontend ↔ Backend Mapping

| Frontend Field | Backend Field | Type | Description |
|---------------|---------------|------|-------------|
| `node_type` | `node_type` | string | Always "waiting" |
| `title` | `title` | string | Node title |
| `answer_type` | `answer_type` | string | Type of answer expected |
| `storage_location` | `storage_type` | string | Where to store the answer |
| `customer_message` | `customer_message` | text | Message sent to customer |
| `max_errors` | `allowed_errors` | integer | Number of allowed errors |
| `response_time_limit` | `response_time_limit_enabled` | boolean | Enable/disable time limit |
| `delay_time` | `response_timeout_amount` | integer | Timeout amount (when enabled) |
| `time_unit` | `response_timeout_unit` | string | Timeout unit (when enabled) |
| `exit_keywords` | `skip_keywords` | array | Keywords to skip this step |

## 🎯 Example 1: Basic Waiting Node (Time Limit OFF)

### Frontend Request Data:
```json
{
  "node_type": "waiting",
  "title": "Get Customer Name",
  "answer_type": "text",
  "storage_location": "user_profile",
  "customer_message": "Please enter your full name:",
  "max_errors": "3",
  "response_time_limit": false,
  "exit_keywords": ["skip", "later"],
  "position_x": 300,
  "position_y": 200,
  "workflow": "workflow-uuid"
}
```

### Backend API Payload:
```json
{
  "node_type": "waiting",
  "title": "Get Customer Name",
  "answer_type": "text",
  "storage_type": "user_profile",
  "storage_field": "full_name",
  "customer_message": "Please enter your full name:",
  "allowed_errors": 3,
  "response_time_limit_enabled": false,
  "skip_keywords": ["skip", "later"],
  "position_x": 300,
  "position_y": 200,
  "workflow": "workflow-uuid"
}
```

## ⏰ Example 2: Waiting Node with Time Limit (Time Limit ON)

### Frontend Request Data:
```json
{
  "node_type": "waiting",
  "title": "Get Customer Email",
  "answer_type": "email",
  "storage_location": "database",
  "customer_message": "Please provide your email address:",
  "max_errors": "2",
  "response_time_limit": true,
  "delay_time": 30,
  "time_unit": "minutes",
  "exit_keywords": [],
  "position_x": 400,
  "position_y": 250,
  "workflow": "workflow-uuid"
}
```

### Backend API Payload:
```json
{
  "node_type": "waiting",
  "title": "Get Customer Email",
  "answer_type": "email",
  "storage_type": "database",
  "storage_field": "email",
  "customer_message": "Please provide your email address:",
  "allowed_errors": 2,
  "response_time_limit_enabled": true,
  "response_timeout_amount": 30,
  "response_timeout_unit": "minutes",
  "skip_keywords": [],
  "position_x": 400,
  "position_y": 250,
  "workflow": "workflow-uuid"
}
```

## 📱 Example 3: Choice Type with Phone Number

### Frontend Request Data:
```json
{
  "node_type": "waiting",
  "title": "Contact Preference",
  "answer_type": "choice",
  "storage_location": "session",
  "customer_message": "How would you like us to contact you?",
  "choice_options": [
    "Phone Call",
    "Text Message", 
    "Email",
    "WhatsApp"
  ],
  "max_errors": "3",
  "response_time_limit": true,
  "delay_time": 60,
  "time_unit": "seconds",
  "exit_keywords": ["skip"],
  "position_x": 500,
  "position_y": 300,
  "workflow": "workflow-uuid"
}
```

### Backend API Payload:
```json
{
  "node_type": "waiting",
  "title": "Contact Preference",
  "answer_type": "choice",
  "storage_type": "session",
  "storage_field": "contact_preference",
  "customer_message": "How would you like us to contact you?",
  "choice_options": [
    "Phone Call",
    "Text Message", 
    "Email",
    "WhatsApp"
  ],
  "allowed_errors": 3,
  "response_time_limit_enabled": true,
  "response_timeout_amount": 60,
  "response_timeout_unit": "seconds",
  "skip_keywords": ["skip"],
  "position_x": 500,
  "position_y": 300,
  "workflow": "workflow-uuid"
}
```

## 🔢 Example 4: Number Input with Custom Field Storage

### Frontend Request Data:
```json
{
  "node_type": "waiting",
  "title": "Rate Our Service",
  "answer_type": "number", 
  "storage_location": "custom_field",
  "customer_message": "Please rate our service from 1 to 10:",
  "max_errors": "2",
  "response_time_limit": true,
  "delay_time": 5,
  "time_unit": "minutes",
  "exit_keywords": ["skip", "later", "no rating"],
  "position_x": 600,
  "position_y": 350,
  "workflow": "workflow-uuid"
}
```

### Backend API Payload:
```json
{
  "node_type": "waiting",
  "title": "Rate Our Service",
  "answer_type": "number",
  "storage_type": "custom_field",
  "storage_field": "service_rating",
  "customer_message": "Please rate our service from 1 to 10:",
  "allowed_errors": 2,
  "response_time_limit_enabled": true,
  "response_timeout_amount": 5,
  "response_timeout_unit": "minutes",
  "skip_keywords": ["skip", "later", "no rating"],
  "position_x": 600,
  "position_y": 350,
  "workflow": "workflow-uuid"
}
```

## 📅 Example 5: Date Input (From Your Screenshot)

### Based on Your Screenshot Data:
```json
{
  "node_type": "waiting",
  "title": "new waiting node",
  "answer_type": "text",
  "storage_location": "database",
  "customer_message": "salam",
  "max_errors": "3",
  "response_time_limit": true,
  "delay_time": 30,
  "time_unit": "minutes",
  "exit_keywords": [],
  "position_x": 100,
  "position_y": 100,
  "workflow": "workflow-uuid"
}
```

### Correct Backend API Payload:
```json
{
  "node_type": "waiting",
  "title": "new waiting node",
  "answer_type": "text",
  "storage_type": "database",
  "storage_field": "user_response",
  "customer_message": "salam",
  "allowed_errors": 3,
  "response_time_limit_enabled": true,
  "response_timeout_amount": 30,
  "response_timeout_unit": "minutes",
  "skip_keywords": [],
  "workflow": "workflow-uuid"
}
```

## 🎯 Frontend Logic for Conditional Fields

### JavaScript Example for Form Handling:

```javascript
const WaitingNodeForm = () => {
  const [formData, setFormData] = useState({
    node_type: 'waiting',
    title: '',
    answer_type: 'text',
    storage_location: 'temporary',
    customer_message: '',
    max_errors: '3',
    response_time_limit: false,
    delay_time: 30,
    time_unit: 'minutes',
    exit_keywords: [],
    choice_options: []
  });

  // Handle response time limit toggle
  const handleTimeLimitToggle = (enabled) => {
    setFormData(prev => ({
      ...prev,
      response_time_limit: enabled,
      // Only include delay_time and time_unit if enabled
      ...(enabled ? {} : { delay_time: null, time_unit: null })
    }));
  };

  // Transform frontend data to backend format
  const transformToBackend = (frontendData) => {
    const backendData = {
      node_type: frontendData.node_type,
      title: frontendData.title,
      answer_type: frontendData.answer_type,
      storage_type: frontendData.storage_location,
      customer_message: frontendData.customer_message,
      allowed_errors: parseInt(frontendData.max_errors),
      response_time_limit_enabled: frontendData.response_time_limit,
      skip_keywords: frontendData.exit_keywords,
      workflow: frontendData.workflow
    };

    // Add storage_field based on storage_type
    if (frontendData.storage_location !== 'temporary') {
      backendData.storage_field = generateStorageField(frontendData.answer_type);
    }

    // Only include timeout fields if time limit is enabled
    if (frontendData.response_time_limit) {
      backendData.response_timeout_amount = frontendData.delay_time;
      backendData.response_timeout_unit = frontendData.time_unit;
    }

    // Add choice options for choice type
    if (frontendData.answer_type === 'choice') {
      backendData.choice_options = frontendData.choice_options;
    }

    return backendData;
  };

  const generateStorageField = (answerType) => {
    const fieldMap = {
      'text': 'text_response',
      'email': 'email',
      'phone': 'phone',
      'number': 'number_response',
      'date': 'date_response',
      'choice': 'choice_response'
    };
    return fieldMap[answerType] || 'user_response';
  };

  return (
    <form>
      {/* Title */}
      <input 
        type="text"
        placeholder="Enter node title"
        value={formData.title}
        onChange={(e) => setFormData(prev => ({...prev, title: e.target.value}))}
      />

      {/* Answer Type */}
      <select 
        value={formData.answer_type}
        onChange={(e) => setFormData(prev => ({...prev, answer_type: e.target.value}))}
      >
        <option value="text">Text</option>
        <option value="email">Email</option>
        <option value="phone">Phone</option>
        <option value="number">Number</option>
        <option value="date">Date</option>
        <option value="choice">Choice</option>
      </select>

      {/* Storage Location */}
      <select 
        value={formData.storage_location}
        onChange={(e) => setFormData(prev => ({...prev, storage_location: e.target.value}))}
      >
        <option value="temporary">Temporary Storage</option>
        <option value="user_profile">User Profile</option>
        <option value="custom_field">Custom Field</option>
        <option value="database">Database</option>
        <option value="session">Session Storage</option>
      </select>

      {/* Customer Message */}
      <textarea 
        placeholder="Enter customer message"
        value={formData.customer_message}
        onChange={(e) => setFormData(prev => ({...prev, customer_message: e.target.value}))}
      />

      {/* Max Errors */}
      <select 
        value={formData.max_errors}
        onChange={(e) => setFormData(prev => ({...prev, max_errors: e.target.value}))}
      >
        <option value="1">1</option>
        <option value="2">2</option>
        <option value="3">3</option>
        <option value="5">5</option>
      </select>

      {/* Response Time Limit Toggle */}
      <label>
        <input 
          type="checkbox"
          checked={formData.response_time_limit}
          onChange={(e) => handleTimeLimitToggle(e.target.checked)}
        />
        Response time limit
      </label>

      {/* Conditional Time Fields - Only show if time limit is enabled */}
      {formData.response_time_limit && (
        <div>
          <input 
            type="number"
            placeholder="30"
            value={formData.delay_time}
            onChange={(e) => setFormData(prev => ({...prev, delay_time: parseInt(e.target.value)}))}
          />
          <select 
            value={formData.time_unit}
            onChange={(e) => setFormData(prev => ({...prev, time_unit: e.target.value}))}
          >
            <option value="seconds">Seconds</option>
            <option value="minutes">Minutes</option>
            <option value="hours">Hours</option>
            <option value="days">Days</option>
          </select>
        </div>
      )}

      {/* Choice Options - Only show for choice type */}
      {formData.answer_type === 'choice' && (
        <div>
          <h4>Choice Options:</h4>
          {formData.choice_options.map((option, index) => (
            <input 
              key={index}
              type="text"
              value={option}
              onChange={(e) => {
                const newOptions = [...formData.choice_options];
                newOptions[index] = e.target.value;
                setFormData(prev => ({...prev, choice_options: newOptions}));
              }}
            />
          ))}
          <button type="button" onClick={() => 
            setFormData(prev => ({...prev, choice_options: [...prev.choice_options, '']}))
          }>
            Add Option
          </button>
        </div>
      )}

      {/* Exit Keywords */}
      <input 
        type="text"
        placeholder="Enter exit keywords (comma separated)"
        onChange={(e) => {
          const keywords = e.target.value.split(',').map(k => k.trim()).filter(k => k);
          setFormData(prev => ({...prev, exit_keywords: keywords}));
        }}
      />

      <button type="submit" onClick={() => {
        const backendData = transformToBackend(formData);
        console.log('Sending to backend:', backendData);
        // Send to API
      }}>
        Save
      </button>
    </form>
  );
};
```

## 🔍 Validation Rules

### Backend Validation (in UnifiedNodeSerializer):

```python
def _validate_waiting_node(self, data):
    """Validate Waiting Node specific fields"""
    answer_type = data.get('answer_type')
    if not answer_type:
        raise serializers.ValidationError({'answer_type': 'Answer type is required for Waiting nodes'})

    if not data.get('customer_message'):
        raise serializers.ValidationError({'customer_message': 'Customer message is required for Waiting nodes'})

    # Validate choice options for choice answer type
    if answer_type == 'choice':
        choice_options = data.get('choice_options', [])
        if not choice_options:
            raise serializers.ValidationError({'choice_options': 'Choice options are required for choice answer type'})
        if len(choice_options) < 2:
            raise serializers.ValidationError({'choice_options': 'At least 2 choice options are required'})

    # Validate storage configuration
    storage_type = data.get('storage_type')
    if storage_type in ['user_profile', 'custom_field', 'database'] and not data.get('storage_field'):
        raise serializers.ValidationError({'storage_field': f'Storage field is required for {storage_type} storage type'})

    # Validate time limit fields
    response_time_limit_enabled = data.get('response_time_limit_enabled', False)
    if response_time_limit_enabled:
        if not data.get('response_timeout_amount'):
            raise serializers.ValidationError({'response_timeout_amount': 'Timeout amount is required when time limit is enabled'})
        if not data.get('response_timeout_unit'):
            raise serializers.ValidationError({'response_timeout_unit': 'Timeout unit is required when time limit is enabled'})
```

## 📊 API Response Examples

### Successful Creation Response:
```json
{
  "id": "waiting-node-uuid",
  "node_type": "waiting",
  "title": "Get Customer Email",
  "answer_type": "email",
  "answer_type_display": "Email",
  "storage_type": "database",
  "storage_type_display": "Database",
  "storage_field": "email",
  "customer_message": "Please provide your email address:",
  "choice_options": [],
  "allowed_errors": 2,
  "skip_keywords": [],
  "response_time_limit_enabled": true,
  "response_timeout_amount": 30,
  "response_timeout_unit": "minutes",
  "response_timeout_unit_display": "Minutes",
  "position_x": 400,
  "position_y": 250,
  "is_active": true,
  "workflow": "workflow-uuid",
  "workflow_name": "Customer Onboarding",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

---

This comprehensive guide shows exactly how to send data for Waiting nodes with proper field mapping and conditional logic for time limit fields!
