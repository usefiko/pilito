# Marketing Workflow Frontend Integration Guide

Complete guide for integrating the Marketing Workflow system with React frontend applications.

## 📋 Table of Contents

- [Overview](#overview)
- [API Authentication](#api-authentication)
- [Core Components](#core-components)
- [Workflow Management](#workflow-management)
- [Visual Workflow Builder](#visual-workflow-builder)
- [Real-time Updates](#real-time-updates)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Marketing Workflow system provides REST APIs that can be easily integrated with React applications to create powerful automation interfaces. This guide covers everything from basic API integration to building a visual workflow editor.

## 🔐 API Authentication

### Setup API Client

```javascript
// api/client.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1/workflow/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

## 🧩 Core Components

### 1. Workflow API Service

```javascript
// services/workflowService.js
import apiClient from '../api/client';

export const workflowService = {
  // Workflows
  async getWorkflows(params = {}) {
    const response = await apiClient.get('/workflows/', { params });
    return response.data;
  },

  async getWorkflow(id) {
    const response = await apiClient.get(`/workflows/${id}/`);
    return response.data;
  },

  async createWorkflow(data) {
    const response = await apiClient.post('/workflows/', data);
    return response.data;
  },

  async updateWorkflow(id, data) {
    const response = await apiClient.put(`/workflows/${id}/`, data);
    return response.data;
  },

  async deleteWorkflow(id) {
    await apiClient.delete(`/workflows/${id}/`);
  },

  // Workflow actions
  async activateWorkflow(id) {
    const response = await apiClient.post(`/workflows/${id}/activate/`);
    return response.data;
  },

  async pauseWorkflow(id) {
    const response = await apiClient.post(`/workflows/${id}/pause/`);
    return response.data;
  },

  async executeWorkflow(id, context) {
    const response = await apiClient.post(`/workflows/${id}/execute/`, { context });
    return response.data;
  },

  // Triggers
  async getTriggers(params = {}) {
    const response = await apiClient.get('/triggers/', { params });
    return response.data;
  },

  async createTrigger(data) {
    const response = await apiClient.post('/triggers/', data);
    return response.data;
  },

  async testTrigger(id, context) {
    const response = await apiClient.post(`/triggers/${id}/test/`, { context });
    return response.data;
  },

  // Actions
  async getActions(params = {}) {
    const response = await apiClient.get('/actions/', { params });
    return response.data;
  },

  async createAction(data) {
    const response = await apiClient.post('/actions/', data);
    return response.data;
  },

  async getActionTypes() {
    const response = await apiClient.get('/actions/action_types/');
    return response.data;
  },

  async testAction(id, context) {
    const response = await apiClient.post(`/actions/${id}/test/`, { context });
    return response.data;
  },

  // Executions
  async getWorkflowExecutions(params = {}) {
    const response = await apiClient.get('/workflow-executions/', { params });
    return response.data;
  },

  async getWorkflowStatistics() {
    const response = await apiClient.get('/workflows/statistics/');
    return response.data;
  },

  // Event processing
  async processEvent(eventData) {
    const response = await apiClient.post('/triggers/process_event/', eventData);
    return response.data;
  }
};
```

### 2. React Hooks for Workflows

```javascript
// hooks/useWorkflows.js
import { useState, useEffect } from 'react';
import { workflowService } from '../services/workflowService';

export const useWorkflows = (filters = {}) => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      const data = await workflowService.getWorkflows(filters);
      setWorkflows(data.results || data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, [JSON.stringify(filters)]);

  const createWorkflow = async (workflowData) => {
    try {
      const newWorkflow = await workflowService.createWorkflow(workflowData);
      setWorkflows(prev => [newWorkflow, ...prev]);
      return newWorkflow;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const updateWorkflow = async (id, data) => {
    try {
      const updated = await workflowService.updateWorkflow(id, data);
      setWorkflows(prev => prev.map(w => w.id === id ? updated : w));
      return updated;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const deleteWorkflow = async (id) => {
    try {
      await workflowService.deleteWorkflow(id);
      setWorkflows(prev => prev.filter(w => w.id !== id));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const activateWorkflow = async (id) => {
    try {
      await workflowService.activateWorkflow(id);
      setWorkflows(prev => prev.map(w => 
        w.id === id ? { ...w, status: 'ACTIVE' } : w
      ));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  return {
    workflows,
    loading,
    error,
    refetch: fetchWorkflows,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    activateWorkflow
  };
};

// hooks/useWorkflowDetail.js
export const useWorkflowDetail = (workflowId) => {
  const [workflow, setWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!workflowId) return;

    const fetchWorkflow = async () => {
      try {
        setLoading(true);
        const data = await workflowService.getWorkflow(workflowId);
        setWorkflow(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchWorkflow();
  }, [workflowId]);

  return { workflow, loading, error, refetch: () => fetchWorkflow() };
};
```

## 📊 Workflow Management Components

### 1. Workflow List Component

```jsx
// components/WorkflowList.jsx
import React, { useState } from 'react';
import { useWorkflows } from '../hooks/useWorkflows';

const WorkflowList = () => {
  const [filters, setFilters] = useState({ status: '' });
  const { workflows, loading, error, activateWorkflow, deleteWorkflow } = useWorkflows(filters);

  const handleStatusFilter = (status) => {
    setFilters({ ...filters, status });
  };

  const handleActivate = async (id) => {
    try {
      await activateWorkflow(id);
      alert('Workflow activated successfully!');
    } catch (err) {
      alert('Failed to activate workflow');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this workflow?')) {
      try {
        await deleteWorkflow(id);
        alert('Workflow deleted successfully!');
      } catch (err) {
        alert('Failed to delete workflow');
      }
    }
  };

  if (loading) return <div className="loading">Loading workflows...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="workflow-list">
      <div className="filters">
        <select 
          value={filters.status} 
          onChange={(e) => handleStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="DRAFT">Draft</option>
          <option value="PAUSED">Paused</option>
        </select>
      </div>

      <div className="workflows">
        {workflows.map(workflow => (
          <WorkflowCard 
            key={workflow.id} 
            workflow={workflow}
            onActivate={() => handleActivate(workflow.id)}
            onDelete={() => handleDelete(workflow.id)}
          />
        ))}
      </div>
    </div>
  );
};

const WorkflowCard = ({ workflow, onActivate, onDelete }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'ACTIVE': return 'green';
      case 'PAUSED': return 'orange';
      case 'DRAFT': return 'gray';
      default: return 'red';
    }
  };

  return (
    <div className="workflow-card">
      <div className="workflow-header">
        <h3>{workflow.name}</h3>
        <span 
          className="status-badge" 
          style={{ backgroundColor: getStatusColor(workflow.status) }}
        >
          {workflow.status}
        </span>
      </div>
      
      <p className="description">{workflow.description}</p>
      
      <div className="workflow-stats">
        <span>Actions: {workflow.actions_count || 0}</span>
        <span>Triggers: {workflow.triggers_count || 0}</span>
        <span>Executions: {workflow.executions_count || 0}</span>
      </div>

      <div className="workflow-actions">
        {workflow.status !== 'ACTIVE' && (
          <button onClick={onActivate} className="btn-activate">
            Activate
          </button>
        )}
        <button onClick={onDelete} className="btn-delete">
          Delete
        </button>
      </div>
    </div>
  );
};

export default WorkflowList;
```

### 2. Workflow Builder Component

```jsx
// components/WorkflowBuilder.jsx
import React, { useState, useEffect } from 'react';
import { workflowService } from '../services/workflowService';

const WorkflowBuilder = ({ workflowId, onSave }) => {
  const [workflow, setWorkflow] = useState({
    name: '',
    description: '',
    status: 'DRAFT'
  });
  const [triggers, setTriggers] = useState([]);
  const [actions, setActions] = useState([]);
  const [availableActions, setAvailableActions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [workflowId]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load workflow if editing
      if (workflowId) {
        const workflowData = await workflowService.getWorkflow(workflowId);
        setWorkflow(workflowData);
        setTriggers(workflowData.triggers || []);
        setActions(workflowData.actions || []);
      }

      // Load available actions
      const actionsData = await workflowService.getActions();
      setAvailableActions(actionsData.results || actionsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      
      const workflowData = {
        ...workflow,
        // Additional workflow configuration
      };

      let savedWorkflow;
      if (workflowId) {
        savedWorkflow = await workflowService.updateWorkflow(workflowId, workflowData);
      } else {
        savedWorkflow = await workflowService.createWorkflow(workflowData);
      }

      onSave?.(savedWorkflow);
    } catch (err) {
      alert('Failed to save workflow');
    } finally {
      setLoading(false);
    }
  };

  const addAction = (actionId) => {
    const action = availableActions.find(a => a.id === actionId);
    if (action) {
      setActions(prev => [...prev, {
        ...action,
        order: prev.length + 1,
        is_required: true
      }]);
    }
  };

  const removeAction = (index) => {
    setActions(prev => prev.filter((_, i) => i !== index));
  };

  const moveAction = (index, direction) => {
    const newActions = [...actions];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (targetIndex >= 0 && targetIndex < newActions.length) {
      [newActions[index], newActions[targetIndex]] = [newActions[targetIndex], newActions[index]];
      setActions(newActions);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="workflow-builder">
      <div className="workflow-form">
        <h2>{workflowId ? 'Edit Workflow' : 'Create New Workflow'}</h2>
        
        <div className="form-group">
          <label>Name:</label>
          <input
            type="text"
            value={workflow.name}
            onChange={(e) => setWorkflow(prev => ({ ...prev, name: e.target.value }))}
            placeholder="Enter workflow name"
          />
        </div>

        <div className="form-group">
          <label>Description:</label>
          <textarea
            value={workflow.description}
            onChange={(e) => setWorkflow(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Enter workflow description"
          />
        </div>

        <div className="form-group">
          <label>Status:</label>
          <select
            value={workflow.status}
            onChange={(e) => setWorkflow(prev => ({ ...prev, status: e.target.value }))}
          >
            <option value="DRAFT">Draft</option>
            <option value="ACTIVE">Active</option>
            <option value="PAUSED">Paused</option>
          </select>
        </div>
      </div>

      <div className="actions-section">
        <h3>Actions</h3>
        
        <div className="add-action">
          <select onChange={(e) => addAction(e.target.value)} value="">
            <option value="">Select an action to add</option>
            {availableActions.map(action => (
              <option key={action.id} value={action.id}>
                {action.name} ({action.action_type})
              </option>
            ))}
          </select>
        </div>

        <div className="actions-list">
          {actions.map((action, index) => (
            <ActionCard
              key={index}
              action={action}
              index={index}
              onRemove={() => removeAction(index)}
              onMoveUp={() => moveAction(index, 'up')}
              onMoveDown={() => moveAction(index, 'down')}
              canMoveUp={index > 0}
              canMoveDown={index < actions.length - 1}
            />
          ))}
        </div>
      </div>

      <div className="builder-actions">
        <button onClick={handleSave} disabled={loading}>
          {loading ? 'Saving...' : 'Save Workflow'}
        </button>
      </div>
    </div>
  );
};

const ActionCard = ({ action, index, onRemove, onMoveUp, onMoveDown, canMoveUp, canMoveDown }) => (
  <div className="action-card">
    <div className="action-header">
      <span className="action-order">{index + 1}</span>
      <h4>{action.name}</h4>
      <span className="action-type">{action.action_type}</span>
    </div>
    
    <p>{action.description}</p>
    
    <div className="action-controls">
      {canMoveUp && <button onClick={onMoveUp}>↑</button>}
      {canMoveDown && <button onClick={onMoveDown}>↓</button>}
      <button onClick={onRemove} className="btn-danger">Remove</button>
    </div>
  </div>
);

export default WorkflowBuilder;
```

## 🎨 Visual Workflow Builder

### React Flow Integration

```jsx
// components/VisualWorkflowBuilder.jsx
import React, { useState, useCallback } from 'react';
import ReactFlow, {
  addEdge,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';

// Custom node types
const TriggerNode = ({ data }) => (
  <div className="trigger-node">
    <div className="node-header">🎯 Trigger</div>
    <div className="node-content">
      <strong>{data.label}</strong>
      <p>{data.triggerType}</p>
    </div>
  </div>
);

const ActionNode = ({ data }) => (
  <div className="action-node">
    <div className="node-header">⚡ Action</div>
    <div className="node-content">
      <strong>{data.label}</strong>
      <p>{data.actionType}</p>
    </div>
  </div>
);

const ConditionNode = ({ data }) => (
  <div className="condition-node">
    <div className="node-header">🔍 Condition</div>
    <div className="node-content">
      <strong>{data.label}</strong>
      <p>{data.operator}</p>
    </div>
  </div>
);

const nodeTypes = {
  trigger: TriggerNode,
  action: ActionNode,
  condition: ConditionNode,
};

const VisualWorkflowBuilder = ({ workflow, onSave }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNodeType, setSelectedNodeType] = useState('action');

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const addNode = useCallback(() => {
    const newNode = {
      id: `${selectedNodeType}-${Date.now()}`,
      type: selectedNodeType,
      position: { x: Math.random() * 300, y: Math.random() * 300 },
      data: {
        label: `New ${selectedNodeType}`,
        triggerType: selectedNodeType === 'trigger' ? 'MESSAGE_RECEIVED' : undefined,
        actionType: selectedNodeType === 'action' ? 'send_message' : undefined,
        operator: selectedNodeType === 'condition' ? 'and' : undefined,
      },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [selectedNodeType, setNodes]);

  const saveWorkflow = async () => {
    try {
      const workflowData = {
        ...workflow,
        ui_settings: {
          nodes: nodes,
          viewport: { x: 0, y: 0, zoom: 1 }
        },
        edges: edges
      };

      await onSave(workflowData);
      alert('Workflow saved successfully!');
    } catch (err) {
      alert('Failed to save workflow');
    }
  };

  return (
    <div className="visual-workflow-builder">
      <div className="toolbar">
        <select 
          value={selectedNodeType} 
          onChange={(e) => setSelectedNodeType(e.target.value)}
        >
          <option value="trigger">Trigger</option>
          <option value="condition">Condition</option>
          <option value="action">Action</option>
        </select>
        <button onClick={addNode}>Add {selectedNodeType}</button>
        <button onClick={saveWorkflow}>Save Workflow</button>
      </div>

      <div className="flow-container" style={{ height: '600px' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <MiniMap />
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
};

export default VisualWorkflowBuilder;
```

## 📊 Analytics Dashboard

```jsx
// components/WorkflowAnalytics.jsx
import React, { useState, useEffect } from 'react';
import { workflowService } from '../services/workflowService';

const WorkflowAnalytics = () => {
  const [statistics, setStatistics] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [statsData, executionsData] = await Promise.all([
        workflowService.getWorkflowStatistics(),
        workflowService.getWorkflowExecutions({ page_size: 10 })
      ]);
      
      setStatistics(statsData);
      setExecutions(executionsData.results || executionsData);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading analytics...</div>;

  return (
    <div className="workflow-analytics">
      <h2>Workflow Analytics</h2>
      
      {statistics && (
        <div className="stats-grid">
          <StatCard 
            title="Total Workflows" 
            value={statistics.total_workflows}
            color="blue"
          />
          <StatCard 
            title="Active Workflows" 
            value={statistics.active_workflows}
            color="green"
          />
          <StatCard 
            title="Total Executions" 
            value={statistics.total_executions}
            color="purple"
          />
          <StatCard 
            title="Success Rate" 
            value={`${Math.round((statistics.successful_executions / statistics.total_executions) * 100)}%`}
            color="orange"
          />
        </div>
      )}

      <div className="recent-executions">
        <h3>Recent Executions</h3>
        <div className="executions-list">
          {executions.map(execution => (
            <ExecutionCard key={execution.id} execution={execution} />
          ))}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, color }) => (
  <div className={`stat-card ${color}`}>
    <h3>{title}</h3>
    <p className="stat-value">{value}</p>
  </div>
);

const ExecutionCard = ({ execution }) => (
  <div className="execution-card">
    <div className="execution-header">
      <h4>{execution.workflow_name}</h4>
      <span className={`status ${execution.status.toLowerCase()}`}>
        {execution.status}
      </span>
    </div>
    <div className="execution-details">
      <p>User: {execution.user || 'N/A'}</p>
      <p>Started: {new Date(execution.created_at).toLocaleString()}</p>
      {execution.duration && (
        <p>Duration: {execution.duration.toFixed(2)}s</p>
      )}
    </div>
  </div>
);

export default WorkflowAnalytics;
```

## 🔄 Real-time Updates

### WebSocket Integration

```javascript
// hooks/useWorkflowWebSocket.js
import { useEffect, useState } from 'react';

export const useWorkflowWebSocket = () => {
  const [socket, setSocket] = useState(null);
  const [workflowUpdates, setWorkflowUpdates] = useState([]);

  useEffect(() => {
    const wsUrl = `ws://localhost:8000/ws/workflows/`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Workflow WebSocket connected');
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setWorkflowUpdates(prev => [data, ...prev.slice(0, 49)]); // Keep last 50 updates
    };

    ws.onclose = () => {
      console.log('Workflow WebSocket disconnected');
      setSocket(null);
    };

    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = (message) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    }
  };

  return { socket, workflowUpdates, sendMessage };
};
```

## 📱 Complete App Example

```jsx
// App.jsx
import React, { useState } from 'react';
import WorkflowList from './components/WorkflowList';
import WorkflowBuilder from './components/WorkflowBuilder';
import VisualWorkflowBuilder from './components/VisualWorkflowBuilder';
import WorkflowAnalytics from './components/WorkflowAnalytics';
import './App.css';

const App = () => {
  const [currentView, setCurrentView] = useState('list');
  const [selectedWorkflowId, setSelectedWorkflowId] = useState(null);

  const handleCreateWorkflow = () => {
    setSelectedWorkflowId(null);
    setCurrentView('builder');
  };

  const handleEditWorkflow = (workflowId) => {
    setSelectedWorkflowId(workflowId);
    setCurrentView('builder');
  };

  const handleWorkflowSaved = () => {
    setCurrentView('list');
    setSelectedWorkflowId(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Marketing Workflow Manager</h1>
        <nav>
          <button 
            className={currentView === 'list' ? 'active' : ''}
            onClick={() => setCurrentView('list')}
          >
            Workflows
          </button>
          <button 
            className={currentView === 'analytics' ? 'active' : ''}
            onClick={() => setCurrentView('analytics')}
          >
            Analytics
          </button>
          <button onClick={handleCreateWorkflow}>
            Create Workflow
          </button>
        </nav>
      </header>

      <main className="app-main">
        {currentView === 'list' && (
          <WorkflowList onEdit={handleEditWorkflow} />
        )}
        
        {currentView === 'builder' && (
          <WorkflowBuilder 
            workflowId={selectedWorkflowId}
            onSave={handleWorkflowSaved}
          />
        )}
        
        {currentView === 'visual' && (
          <VisualWorkflowBuilder 
            workflowId={selectedWorkflowId}
            onSave={handleWorkflowSaved}
          />
        )}
        
        {currentView === 'analytics' && (
          <WorkflowAnalytics />
        )}
      </main>
    </div>
  );
};

export default App;
```

## 🎨 CSS Styles

```css
/* App.css */
.app {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.app-header {
  background: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-header nav button {
  margin-left: 1rem;
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.app-header nav button.active,
.app-header nav button:hover {
  background: #007bff;
  color: white;
}

.workflow-list {
  padding: 2rem;
}

.workflows {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.workflow-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  color: white;
  font-size: 0.8rem;
  font-weight: bold;
}

.workflow-stats {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
  font-size: 0.9rem;
  color: #666;
}

.workflow-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-activate {
  background: #28a745;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.btn-delete {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.workflow-builder {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.actions-section {
  margin-top: 2rem;
}

.action-card {
  background: #f8f9fa;
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 4px;
  border-left: 4px solid #007bff;
}

.action-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.action-order {
  background: #007bff;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: bold;
}

.action-type {
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-card.blue { border-top: 4px solid #007bff; }
.stat-card.green { border-top: 4px solid #28a745; }
.stat-card.purple { border-top: 4px solid #6f42c1; }
.stat-card.orange { border-top: 4px solid #fd7e14; }

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  margin: 0;
}

.execution-card {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
}

.status.completed { background: #d4edda; color: #155724; }
.status.running { background: #d1ecf1; color: #0c5460; }
.status.failed { background: #f8d7da; color: #721c24; }
.status.pending { background: #fff3cd; color: #856404; }

/* Visual workflow builder styles */
.visual-workflow-builder {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.toolbar {
  background: white;
  padding: 1rem;
  display: flex;
  gap: 1rem;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.flow-container {
  flex: 1;
}

.trigger-node,
.action-node,
.condition-node {
  background: white;
  border: 2px solid #ddd;
  border-radius: 8px;
  padding: 0.5rem;
  min-width: 150px;
}

.trigger-node { border-color: #28a745; }
.action-node { border-color: #007bff; }
.condition-node { border-color: #ffc107; }

.node-header {
  background: #f8f9fa;
  padding: 0.25rem 0.5rem;
  margin: -0.5rem -0.5rem 0.5rem -0.5rem;
  border-radius: 6px 6px 0 0;
  font-size: 0.8rem;
  font-weight: bold;
}

.node-content p {
  margin: 0;
  font-size: 0.8rem;
  color: #666;
}
```

## 🚀 Best Practices

### 1. Error Handling
```javascript
// utils/errorHandler.js
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const message = error.response.data?.message || 'Server error occurred';
    console.error('API Error:', message);
    return message;
  } else if (error.request) {
    // Request was made but no response received
    console.error('Network Error:', error.message);
    return 'Network error - please check your connection';
  } else {
    // Something else happened
    console.error('Error:', error.message);
    return 'An unexpected error occurred';
  }
};
```

### 2. Performance Optimization
```javascript
// Debounce API calls
import { debounce } from 'lodash';

const debouncedSearch = debounce(async (query) => {
  const results = await workflowService.getWorkflows({ search: query });
  setSearchResults(results);
}, 300);

// Memoize expensive calculations
import { useMemo } from 'react';

const workflowStats = useMemo(() => {
  return workflows.reduce((acc, workflow) => {
    acc[workflow.status] = (acc[workflow.status] || 0) + 1;
    return acc;
  }, {});
}, [workflows]);
```

### 3. Security Considerations
```javascript
// Validate user permissions
const canEditWorkflow = (workflow, user) => {
  return user.is_staff || workflow.created_by === user.id;
};

// Sanitize user input
import DOMPurify from 'dompurify';

const sanitizeInput = (input) => {
  return DOMPurify.sanitize(input);
};
```

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure Django CORS settings allow your frontend domain
   - Check that `CORS_ALLOWED_ORIGINS` includes your React app URL

2. **Authentication Issues**
   - Verify JWT tokens are properly stored and sent
   - Check token expiration and refresh logic

3. **WebSocket Connection Problems**
   - Confirm WebSocket URL is correct
   - Check Django Channels configuration

4. **API Rate Limiting**
   - Implement request throttling in frontend
   - Add loading states to prevent multiple requests

### Debug Tools
```javascript
// API request logger
apiClient.interceptors.request.use((config) => {
  console.log('API Request:', config.method.toUpperCase(), config.url);
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.config?.url);
    return Promise.reject(error);
  }
);
```

## 📚 Additional Resources

- [React Flow Documentation](https://reactflow.dev/)
- [Axios Documentation](https://axios-http.com/)
- [React Hooks Guide](https://reactjs.org/docs/hooks-intro.html)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

This guide provides everything needed to build a comprehensive React frontend for the Marketing Workflow system. The components are modular and can be customized based on your specific UI requirements and design system.
