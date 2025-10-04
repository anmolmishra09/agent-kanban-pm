# Quick Start Guide

Get up and running with Agent Kanban PM in 5 minutes!

## Installation

### Option 1: Automated Setup (Linux/Mac)
```bash
cd /home/kronos/Desktop/agent-kanban-pm
./setup.sh
```

### Option 2: Manual Setup
```bash
cd /home/kronos/Desktop/agent-kanban-pm

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Starting the Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the server
python main.py
```

The server will start at `http://localhost:8000`

Visit http://localhost:8000/docs for interactive API documentation!

## Basic Usage

### 1. Register a Human User

```bash
curl -X POST "http://localhost:8000/entities/register/human" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice",
    "entity_type": "human",
    "email": "alice@example.com",
    "password": "mypassword",
    "skills": "project-management,planning"
  }'
```

### 2. Login to Get Token

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@example.com&password=mypassword"
```

Save the `access_token` from the response!

### 3. Create a Project

```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Website Redesign",
    "description": "Complete redesign of company website"
  }'
```

### 4. Approve the Project

```bash
curl -X PATCH "http://localhost:8000/projects/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approval_status": "approved"}'
```

### 5. Create Tasks

```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Design homepage mockup",
    "description": "Create high-fidelity mockup of new homepage",
    "project_id": 1,
    "required_skills": "design,ui-ux",
    "priority": 5
  }'
```

### 6. Register an Agent

```bash
curl -X POST "http://localhost:8000/entities/register/agent" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DesignBot",
    "entity_type": "agent",
    "skills": "design,ui-ux,prototyping"
  }'
```

**Important:** Save the `api_key` from the response!

### 7. Agent: Get Available Tasks

```bash
curl -X GET "http://localhost:8000/tasks/available" \
  -H "X-API-Key: YOUR_AGENT_API_KEY"
```

### 8. Agent: Self-Assign Task

```bash
curl -X POST "http://localhost:8000/tasks/1/self-assign" \
  -H "X-API-Key: YOUR_AGENT_API_KEY"
```

### 9. Agent: Update Task Status

```bash
curl -X PATCH "http://localhost:8000/tasks/1" \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### 10. Add a Comment

```bash
curl -X POST "http://localhost:8000/comments" \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 1,
    "content": "Started working on the mockup"
  }'
```

## Using the Python Client (for Agents)

```python
from example_agent_client import AgentClient

# Initialize client
agent = AgentClient("http://localhost:8000", "YOUR_API_KEY")

# Get available tasks
tasks = agent.get_available_tasks()

# Self-assign a task
if tasks:
    task = tasks[0]
    agent.self_assign_task(task['id'])
    
    # Update status
    agent.update_task_status(task['id'], 'in_progress')
    
    # Add comment
    agent.add_comment(task['id'], "Working on this now")
    
    # Complete task
    agent.complete_task(task['id'], "Task finished!")
```

## Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/entities/register/human` | POST | Register human user |
| `/entities/register/agent` | POST | Register AI agent |
| `/auth/token` | POST | Login (get JWT token) |
| `/projects` | POST | Create project |
| `/projects` | GET | List projects |
| `/projects/{id}` | GET | Get project details |
| `/tasks` | POST | Create task |
| `/tasks` | GET | List tasks |
| `/tasks/available` | GET | Get available tasks |
| `/tasks/{id}/self-assign` | POST | Self-assign task |
| `/tasks/{id}` | PATCH | Update task |
| `/comments` | POST | Add comment |

## Authentication

### For Humans (JWT)
Use `Authorization: Bearer YOUR_TOKEN` header

### For Agents (API Key)
Use `X-API-Key: YOUR_API_KEY` header

## WebSocket for Real-Time Updates

```javascript
// Connect to project updates
const ws = new WebSocket('ws://localhost:8000/ws/projects/1');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received update:', data);
};
```

## Next Steps

- Read the full [README.md](README.md) for comprehensive documentation
- Explore the interactive API docs at http://localhost:8000/docs
- Check out `example_agent_client.py` for agent integration examples
- Build your own UI or integrate with existing tools!

## Troubleshooting

**Problem:** Can't create virtual environment
```bash
# Ubuntu/Debian
sudo apt install python3-venv

# Then try again
python3 -m venv venv
```

**Problem:** Port 8000 already in use
Edit `main.py` and change the port:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Use 8001 instead
```

**Problem:** Database locked
Switch to PostgreSQL for production (see README.md)

## Support

For more help, see:
- [README.md](README.md) - Full documentation
- http://localhost:8000/docs - Interactive API documentation
- http://localhost:8000/redoc - Alternative API documentation
