# Logging Configuration Guide

This document explains the logging setup for the Fiko Backend application and how to manage log verbosity.

## Problem Solved

The original logs were extremely verbose with DEBUG-level messages from:
- Django Channels WebSocket consumers 
- Daphne WebSocket protocol handlers
- WebSocket authentication middleware
- Repetitive connection/disconnection cycles

## Changes Made

### 1. Development Environment (`src/core/settings/development.py`)

**Key Changes:**
- Console logging level raised from DEBUG to INFO
- Specific loggers configured for different components
- Daphne WebSocket protocol logs suppressed (WARNING level)
- WebSocket consumer logs reduced to INFO level
- Authentication middleware logs reduced to WARNING level

**Benefits:**
- Significantly fewer console logs during development
- Important information still visible
- Debug logs still saved to file (`/tmp/debug.log`)

### 2. Production Environment (`src/core/settings/production.py`)

**Key Changes:**
- Console shows only WARNING level and above
- Rotating file handler with 10MB max size and 5 backups
- Most verbose logs suppressed completely
- Critical errors and warnings still logged

### 3. WebSocket Consumers (`src/message/consumers.py`)

**Changes:**
- Connection/disconnection logs changed from INFO to DEBUG
- User authentication logs changed from INFO to DEBUG
- Conversation/customer update logs changed from INFO to DEBUG
- Important business logic still logged at INFO level

### 4. Authentication Middleware (`src/message/middleware/websocket_auth.py`)

**Changes:**
- Token validation logs changed from WARNING to DEBUG
- Connection attempt logs disabled
- Authentication errors reduced to DEBUG in development
- Only critical errors remain at ERROR level

## Log Levels Guide

### Development Environment
- **ERROR**: Critical errors that need immediate attention
- **WARNING**: Important issues that should be reviewed
- **INFO**: Key business events (user actions, API calls)
- **DEBUG**: Detailed technical information (saved to file only)

### Production Environment
- **ERROR**: Critical errors requiring immediate action
- **WARNING**: Important issues for monitoring
- **INFO**: Key business events for audit trails
- **DEBUG**: Not logged in production

## Directory Setup for Production

Create the log directory on your production server:

```bash
sudo mkdir -p /var/log/fiko
sudo chown www-data:www-data /var/log/fiko  # or your app user
sudo chmod 755 /var/log/fiko
```

## Environment-Specific Configurations

### For Heavy Debugging (Temporary)
Add to your development settings:
```python
# Temporary debug mode - very verbose
LOGGING['loggers']['']['level'] = 'DEBUG'
LOGGING['handlers']['console']['level'] = 'DEBUG'
```

### For Production Monitoring
The production config includes:
- Rotating log files to prevent disk space issues
- Only critical and important messages in console
- Structured logging for potential log aggregation tools

## Log Analysis

### Common Log Patterns After Changes

**Before (Verbose):**
```
message.consumers DEBUG    User 31 marked as globally offline
daphne.ws_protocol DEBUG   Sent WebSocket packet to client
message.middleware.websocket_auth ERROR    Error authenticating WebSocket token
```

**After (Clean):**
```
message.consumers INFO     User authentication failed
message.api WARNING        Rate limit exceeded for user 31
accounts.api ERROR         Database connection failed
```

### Monitoring Important Events

You should still see:
- Authentication failures (ERROR level)
- Rate limiting events (WARNING level)  
- Business logic errors (ERROR level)
- Important user actions (INFO level)

## Troubleshooting

### If You Need More Verbose Logs Temporarily

1. **Enable debug for specific module:**
```python
LOGGING['loggers']['message.consumers']['level'] = 'DEBUG'
```

2. **Enable debug for all WebSocket events:**
```python
LOGGING['loggers']['daphne']['level'] = 'DEBUG'
```

3. **Revert to original verbose setup:**
```python
LOGGING['loggers']['']['level'] = 'DEBUG'
LOGGING['handlers']['console']['level'] = 'DEBUG'
```

### Log File Management

- Development logs: `/tmp/debug.log` (temporary)
- Production logs: `/var/log/fiko/app.log` (rotating)
- Log rotation: Automatic (5 files, 10MB each)

## Best Practices

1. Use INFO for business events users should know about
2. Use WARNING for recoverable issues that need attention  
3. Use ERROR for failures that affect functionality
4. Use DEBUG for detailed technical information
5. Avoid logging sensitive information (tokens, passwords)
6. Use structured logging for production systems

## Performance Impact

The logging changes should significantly improve:
- Console readability during development
- Application performance (fewer I/O operations)
- Log storage requirements in production
- Debugging efficiency (focused on important events)