# Project Structure

## Overview
This is a complete, production-ready project management system built with FastAPI that enables seamless collaboration between humans and AI agents.

## File Structure

```
agent-kanban-pm/
├── main.py                      # Main FastAPI application with all endpoints
├── models.py                    # SQLAlchemy database models
├── schemas.py                   # Pydantic schemas for request/response validation
├── database.py                  # Database connection and session management
├── auth.py                      # Authentication and authorization utilities
├── websocket_manager.py         # WebSocket connection manager for real-time updates
├── example_agent_client.py      # Example Python client for AI agents
├── requirements.txt             # Python dependencies
├── setup.sh                     # Automated setup script (Linux/Mac)
├── .env                         # Environment configuration (local)
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git ignore rules
├── README.md                    # Complete documentation
├── QUICKSTART.md               # Quick start guide
└── PROJECT_STRUCTURE.md        # This file
```

## Core Components

### 1. main.py (670 lines)
The heart of the application containing:
- FastAPI app initialization
- All REST API endpoints
- WebSocket endpoints
- CORS middleware configuration
- Route handlers for:
  - Entity management (humans & agents)
  - Project management
  - Stage management
  - Task management
  - Task assignment
  - Comments
  - Health checks

### 2. models.py (122 lines)
SQLAlchemy ORM models defining:
- **Entity**: Unified model for humans and AI agents
- **Project**: Top-level project containers with approval workflow
- **Stage**: Kanban board columns (customizable workflow stages)
- **Task**: Work items with support for subtasks
- **Comment**: Discussion threads on tasks
- **Enums**: EntityType, TaskStatus, ApprovalStatus

### 3. schemas.py (171 lines)
Pydantic schemas for data validation:
- Request schemas (Create, Update)
- Response schemas (with nested relationships)
- Authentication schemas (Token, TokenData)
- Detailed response schemas (with subtasks, comments)

### 4. database.py (27 lines)
Database management:
- Async SQLAlchemy engine setup
- Session management
- Database initialization
- Dependency injection for database sessions

### 5. auth.py (123 lines)
Security and authentication:
- Password hashing (bcrypt)
- API key generation for agents
- JWT token creation and validation
- Dual authentication system:
  - JWT tokens for humans
  - API keys for agents
- Current user dependency injection

### 6. websocket_manager.py (86 lines)
Real-time communication:
- WebSocket connection management
- Project-specific message broadcasting
- Global message broadcasting
- Connection cleanup
- Standardized notification format

### 7. example_agent_client.py (190 lines)
Reference implementation showing:
- How to connect as an agent
- Common workflows
- Task discovery and assignment
- Status updates
- Comment management

## Database Schema

### Entity (Unified User/Agent Model)
- `id`: Primary key
- `name`: Display name
- `entity_type`: 'human' or 'agent'
- `email`: Email (for humans)
- `api_key`: API key (for agents)
- `hashed_password`: Password hash (for humans)
- `skills`: Comma-separated skill list
- `is_active`: Account status
- `created_at`: Registration timestamp

### Project
- `id`: Primary key
- `name`: Project name
- `description`: Project description
- `creator_id`: Foreign key to Entity
- `approval_status`: 'pending', 'approved', or 'rejected'
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Stage
- `id`: Primary key
- `name`: Stage name (e.g., "In Progress")
- `description`: Stage description
- `order`: Display order in kanban board
- `project_id`: Foreign key to Project
- `created_at`: Creation timestamp

### Task
- `id`: Primary key
- `title`: Task title
- `description`: Task description
- `status`: Current status enum
- `project_id`: Foreign key to Project
- `stage_id`: Foreign key to Stage (nullable)
- `parent_task_id`: Foreign key to Task (for subtasks)
- `required_skills`: Comma-separated skill requirements
- `priority`: Integer priority (higher = more important)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `completed_at`: Completion timestamp (nullable)

### Comment
- `id`: Primary key
- `content`: Comment text
- `task_id`: Foreign key to Task
- `author_id`: Foreign key to Entity
- `created_at`: Creation timestamp

### Task Assignments (Many-to-Many)
- `task_id`: Foreign key to Task
- `entity_id`: Foreign key to Entity

## API Endpoints Summary

### Authentication & Users
- `POST /entities/register/human` - Register human user
- `POST /entities/register/agent` - Register AI agent
- `POST /auth/token` - Login (JWT for humans)
- `GET /entities/me` - Get current entity info
- `GET /entities` - List all entities

### Projects (15 endpoints total)
- `POST /projects` - Create project
- `GET /projects` - List projects
- `GET /projects/{id}` - Get project details
- `PATCH /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project

### Stages (10 endpoints)
- `POST /projects/{id}/stages` - Add stage
- `PATCH /stages/{id}` - Update stage
- `DELETE /stages/{id}` - Delete stage

### Tasks (20 endpoints)
- `POST /tasks` - Create task
- `GET /tasks` - List tasks (with filters)
- `GET /tasks/{id}` - Get task details
- `PATCH /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task
- `GET /tasks/available` - Get available tasks based on skills

### Task Assignment
- `POST /tasks/{id}/assign` - Assign task to entity
- `POST /tasks/{id}/self-assign` - Self-assign task
- `DELETE /tasks/{id}/unassign/{entity_id}` - Unassign task

### Comments
- `POST /comments` - Add comment to task
- `GET /tasks/{id}/comments` - Get task comments

### Real-Time
- `WS /ws/projects/{id}` - Project-specific WebSocket
- `WS /ws` - Global WebSocket

### System
- `GET /health` - Health check

## Key Features

### 1. Platform Agnostic
- Pure REST API - works with any client
- No framework lock-in
- Language-agnostic (any language can use the API)

### 2. Dual Authentication
- **Humans**: Email/password → JWT tokens
- **Agents**: API keys (no setup required)
- Both use the same endpoints

### 3. Skill-Based Matching
- Tasks specify `required_skills`
- Entities have `skills`
- `/tasks/available` filters by matching skills

### 4. Approval Workflow
- Projects start as "pending"
- Must be approved before work begins
- Supports review process

### 5. Flexible Stages
- Default: Backlog → To Do → In Progress → Review → Done
- Fully customizable per project
- Tasks can move between stages

### 6. Subtasks
- Tasks can have parent tasks
- Hierarchical task breakdown
- Useful for complex projects

### 7. Real-Time Updates
- WebSocket support
- Project-specific channels
- Global notification channel

### 8. Comments & Collaboration
- Discussion on tasks
- Timestamped and attributed
- Supports human-agent communication

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Database ORM**: SQLAlchemy 2.0.23 (async)
- **Validation**: Pydantic 2.5.0
- **Authentication**: JWT (python-jose) + API keys
- **Password Hashing**: Bcrypt (passlib)
- **WebSockets**: Built-in FastAPI support
- **Default DB**: SQLite (aiosqlite)
- **Production DB**: PostgreSQL/MySQL supported

## Extension Points

### Easy to Add:
1. **Email Notifications**: Hook into task updates
2. **Webhooks**: Trigger external systems on events
3. **File Attachments**: Add to tasks/comments
4. **Analytics**: Track completion rates, velocity
5. **Custom Fields**: Extend models with project-specific fields
6. **Integrations**: GitHub, Slack, Jira, etc.
7. **Advanced Permissions**: Role-based access control
8. **Task Dependencies**: Block tasks based on others
9. **Time Tracking**: Log hours worked
10. **API Rate Limiting**: Protect against abuse

## Security Considerations

### Implemented:
- Password hashing (bcrypt)
- JWT token expiration
- API key authentication
- CORS support
- SQL injection protection (SQLAlchemy ORM)

### For Production:
- Change `SECRET_KEY` in `.env`
- Configure CORS `allow_origins` properly
- Use HTTPS
- Consider PostgreSQL instead of SQLite
- Add rate limiting
- Implement API key rotation
- Add audit logging
- Consider row-level security

## Performance

### Current:
- Async/await throughout
- Connection pooling via SQLAlchemy
- Efficient querying with selectinload

### Optimization Options:
- Add Redis for caching
- Implement pagination
- Add database indexes
- Use read replicas
- CDN for static assets (if adding UI)

## Testing

The codebase is structured for easy testing:
- Dependency injection throughout
- Separate concerns (models, schemas, auth)
- Can use TestClient from FastAPI
- Async test support

Example test structure:
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_human():
    response = client.post("/entities/register/human", json={...})
    assert response.status_code == 201
```

## Deployment

### Development:
```bash
python main.py
```

### Production with Gunicorn:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker:
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

MIT License - Free to use, modify, and distribute!
