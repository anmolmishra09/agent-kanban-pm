from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import timedelta, datetime

from database import get_db, init_db
from models import Entity, Project, Task, Stage, Comment, EntityType, TaskStatus, ApprovalStatus
from schemas import (
    EntityCreate, EntityResponse, ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectDetailResponse, TaskCreate, TaskUpdate, TaskResponse, TaskDetailResponse,
    StageCreate, StageUpdate, StageResponse, CommentCreate, CommentResponse,
    TaskAssignment, Token
)
from auth import (
    get_password_hash, generate_api_key, authenticate_entity, create_access_token,
    get_current_active_entity, ACCESS_TOKEN_EXPIRE_MINUTES
)
from websocket_manager import manager, create_notification

app = FastAPI(
    title="Agent Kanban Project Management API",
    description="A platform-agnostic project management system for humans and AI agents",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS middleware for UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()


# ============================================================================
# UI ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Dashboard page"""
    # Get stats
    total_projects = await db.execute(select(func.count(Project.id)))
    total_tasks = await db.execute(select(func.count(Task.id)))
    completed_tasks = await db.execute(select(func.count(Task.id)).where(Task.status == TaskStatus.COMPLETED))
    total_entities = await db.execute(select(func.count(Entity.id)))
    
    stats = {
        "total_projects": total_projects.scalar(),
        "total_tasks": total_tasks.scalar(),
        "completed_tasks": completed_tasks.scalar(),
        "total_entities": total_entities.scalar()
    }
    
    # Get recent projects
    result = await db.execute(
        select(Project).order_by(Project.created_at.desc()).limit(5)
    )
    recent_projects = result.scalars().all()
    
    # Add task count to projects
    for project in recent_projects:
        task_count_result = await db.execute(
            select(func.count(Task.id)).where(Task.project_id == project.id)
        )
        project.task_count = task_count_result.scalar()
    
    # Get recent tasks
    result = await db.execute(
        select(Task).order_by(Task.created_at.desc()).limit(6)
    )
    recent_tasks = result.scalars().all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_projects": recent_projects,
        "recent_tasks": recent_tasks
    })


@app.get("/ui/projects", response_class=HTMLResponse, include_in_schema=False)
async def ui_projects(request: Request, db: AsyncSession = Depends(get_db)):
    """Projects list page"""
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.stages), selectinload(Project.tasks))
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "projects": projects
    })


@app.get("/ui/projects/{project_id}/board", response_class=HTMLResponse, include_in_schema=False)
async def project_kanban_board(request: Request, project_id: int, db: AsyncSession = Depends(get_db)):
    """Kanban board for a project"""
    result = await db.execute(
        select(Project)
        .filter(Project.id == project_id)
        .options(
            selectinload(Project.stages).selectinload(Stage.tasks).selectinload(Task.assignees)
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return templates.TemplateResponse("kanban_board.html", {
        "request": request,
        "project": project
    })


# ============================================================================
# ENTITY MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/entities/register/human", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def register_human(entity: EntityCreate, db: AsyncSession = Depends(get_db)):
    """Register a new human user"""
    if entity.entity_type != EntityType.HUMAN:
        raise HTTPException(status_code=400, detail="Entity type must be 'human'")
    
    if not entity.email or not entity.password:
        raise HTTPException(status_code=400, detail="Email and password required for humans")
    
    # Check if email already exists
    result = await db.execute(select(Entity).filter(Entity.email == entity.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_entity = Entity(
        name=entity.name,
        entity_type=EntityType.HUMAN,
        email=entity.email,
        hashed_password=get_password_hash(entity.password),
        skills=entity.skills
    )
    db.add(db_entity)
    await db.commit()
    await db.refresh(db_entity)
    return db_entity


@app.post("/entities/register/agent", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_agent(entity: EntityCreate, db: AsyncSession = Depends(get_db)):
    """Register a new agent and return API key"""
    if entity.entity_type != EntityType.AGENT:
        raise HTTPException(status_code=400, detail="Entity type must be 'agent'")
    
    api_key = generate_api_key()
    
    db_entity = Entity(
        name=entity.name,
        entity_type=EntityType.AGENT,
        email=entity.email,
        api_key=api_key,
        skills=entity.skills
    )
    db.add(db_entity)
    await db.commit()
    await db.refresh(db_entity)
    
    return {
        "id": db_entity.id,
        "name": db_entity.name,
        "entity_type": db_entity.entity_type,
        "api_key": api_key,
        "message": "Agent registered successfully. Save the API key securely."
    }


@app.post("/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login endpoint for humans to get JWT token"""
    entity = await authenticate_entity(db, form_data.username, form_data.password)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(entity.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/entities/me", response_model=EntityResponse)
async def get_current_entity_info(current_entity: Entity = Depends(get_current_active_entity)):
    """Get current authenticated entity information"""
    return current_entity


@app.get("/entities", response_model=List[EntityResponse])
async def list_entities(
    entity_type: Optional[EntityType] = None,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """List all entities, optionally filtered by type"""
    query = select(Entity).filter(Entity.is_active == True)
    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)
    
    result = await db.execute(query)
    entities = result.scalars().all()
    return entities


# ============================================================================
# PROJECT MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Create a new project (requires approval)"""
    db_project = Project(
        name=project.name,
        description=project.description,
        creator_id=current_entity.id,
        approval_status=ApprovalStatus.PENDING
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    
    # Create default stages
    default_stages = [
        {"name": "Backlog", "description": "Tasks to be done", "order": 1},
        {"name": "To Do", "description": "Ready to start", "order": 2},
        {"name": "In Progress", "description": "Currently being worked on", "order": 3},
        {"name": "Review", "description": "Awaiting review", "order": 4},
        {"name": "Done", "description": "Completed tasks", "order": 5}
    ]
    
    for stage_data in default_stages:
        stage = Stage(project_id=db_project.id, **stage_data)
        db.add(stage)
    
    await db.commit()
    await db.refresh(db_project)
    return db_project


@app.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    approval_status: Optional[ApprovalStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """List all projects, optionally filtered by approval status"""
    query = select(Project)
    if approval_status:
        query = query.filter(Project.approval_status == approval_status)
    
    result = await db.execute(query.order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return projects


@app.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Get detailed project information including stages and tasks"""
    result = await db.execute(
        select(Project)
        .filter(Project.id == project_id)
        .options(selectinload(Project.stages), selectinload(Project.tasks))
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@app.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Update project details or approval status"""
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(project)
    return project


@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Delete a project"""
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()


# ============================================================================
# STAGE MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/projects/{project_id}/stages", response_model=StageResponse, status_code=status.HTTP_201_CREATED)
async def create_stage(
    project_id: int,
    stage: StageCreate,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Add a new stage to a project"""
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_stage = Stage(project_id=project_id, **stage.model_dump())
    db.add(db_stage)
    await db.commit()
    await db.refresh(db_stage)
    return db_stage


@app.patch("/stages/{stage_id}", response_model=StageResponse)
async def update_stage(
    stage_id: int,
    stage_update: StageUpdate,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Update stage details"""
    result = await db.execute(select(Stage).filter(Stage.id == stage_id))
    stage = result.scalar_one_or_none()
    
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    update_data = stage_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stage, field, value)
    
    await db.commit()
    await db.refresh(stage)
    return stage


@app.delete("/stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stage(
    stage_id: int,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Delete a stage"""
    result = await db.execute(select(Stage).filter(Stage.id == stage_id))
    stage = result.scalar_one_or_none()
    
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    await db.delete(stage)
    await db.commit()


# ============================================================================
# TASK MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Create a new task or subtask"""
    # Verify project exists
    result = await db.execute(select(Project).filter(Project.id == task.project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_task = Task(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task, ["assignees"])
    return db_task


@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[int] = None,
    stage_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    assigned_to_me: bool = False,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """List tasks with optional filters"""
    query = select(Task).options(selectinload(Task.assignees))
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if stage_id:
        query = query.filter(Task.stage_id == stage_id)
    if status:
        query = query.filter(Task.status == status)
    
    result = await db.execute(query.order_by(Task.priority.desc(), Task.created_at.desc()))
    tasks = result.scalars().all()
    
    if assigned_to_me:
        tasks = [task for task in tasks if current_entity in task.assignees]
    
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Get detailed task information including subtasks and comments"""
    result = await db.execute(
        select(Task)
        .filter(Task.id == task_id)
        .options(
            selectinload(Task.assignees),
            selectinload(Task.subtasks),
            selectinload(Task.comments)
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Update task details"""
    result = await db.execute(
        select(Task).filter(Task.id == task_id).options(selectinload(Task.assignees))
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # Mark as completed if status changed to completed
    if task_update.status == TaskStatus.COMPLETED and task.completed_at is None:
        task.completed_at = datetime.utcnow()
    
    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Delete a task"""
    result = await db.execute(select(Task).filter(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()


# ============================================================================
# TASK ASSIGNMENT ENDPOINTS
# ============================================================================

@app.post("/tasks/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: int,
    entity_id: int,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Assign a task to an entity (human or agent)"""
    result = await db.execute(
        select(Task).filter(Task.id == task_id).options(selectinload(Task.assignees))
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    entity_result = await db.execute(select(Entity).filter(Entity.id == entity_id))
    entity = entity_result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    if entity not in task.assignees:
        task.assignees.append(entity)
        await db.commit()
        await db.refresh(task)
    
    return task


@app.post("/tasks/{task_id}/self-assign", response_model=TaskResponse)
async def self_assign_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Self-assign a task"""
    result = await db.execute(
        select(Task).filter(Task.id == task_id).options(selectinload(Task.assignees))
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if current_entity not in task.assignees:
        task.assignees.append(current_entity)
        await db.commit()
        await db.refresh(task)
    
    return task


@app.delete("/tasks/{task_id}/unassign/{entity_id}", response_model=TaskResponse)
async def unassign_task(
    task_id: int,
    entity_id: int,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Unassign an entity from a task"""
    result = await db.execute(
        select(Task).filter(Task.id == task_id).options(selectinload(Task.assignees))
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    entity_result = await db.execute(select(Entity).filter(Entity.id == entity_id))
    entity = entity_result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    if entity in task.assignees:
        task.assignees.remove(entity)
        await db.commit()
        await db.refresh(task)
    
    return task


@app.get("/tasks/available", response_model=List[TaskResponse])
async def get_available_tasks(
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Get tasks available for the current entity based on skills"""
    query = select(Task).options(selectinload(Task.assignees)).filter(
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
    )
    
    result = await db.execute(query)
    all_tasks = result.scalars().all()
    
    # Filter tasks where entity has matching skills
    available_tasks = []
    entity_skills = set(current_entity.skills.split(',')) if current_entity.skills else set()
    
    for task in all_tasks:
        if not task.required_skills:
            available_tasks.append(task)
        else:
            task_skills = set(task.required_skills.split(','))
            if entity_skills & task_skills:  # If there's any skill match
                available_tasks.append(task)
    
    return available_tasks


# ============================================================================
# COMMENT ENDPOINTS
# ============================================================================

@app.post("/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Add a comment to a task"""
    result = await db.execute(select(Task).filter(Task.id == comment.task_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")
    
    db_comment = Comment(
        content=comment.content,
        task_id=comment.task_id,
        author_id=current_entity.id
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment


@app.get("/tasks/{task_id}/comments", response_model=List[CommentResponse])
async def get_task_comments(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_entity: Entity = Depends(get_current_active_entity)
):
    """Get all comments for a task"""
    result = await db.execute(
        select(Comment)
        .filter(Comment.task_id == task_id)
        .order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()
    return comments


# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@app.websocket("/ws/projects/{project_id}")
async def websocket_project_updates(websocket: WebSocket, project_id: int):
    """WebSocket endpoint for real-time project updates"""
    await manager.connect(websocket, project_id)
    try:
        # Send initial connection message
        await manager.send_personal_message(
            {"type": "connection", "message": f"Connected to project {project_id}"},
            websocket
        )
        
        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle specific commands if needed
            await manager.send_personal_message(
                {"type": "echo", "message": data},
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, project_id)


@app.websocket("/ws")
async def websocket_global_updates(websocket: WebSocket):
    """WebSocket endpoint for global updates"""
    await manager.connect(websocket)
    try:
        # Send initial connection message
        await manager.send_personal_message(
            {"type": "connection", "message": "Connected to global updates"},
            websocket
        )
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(
                {"type": "echo", "message": data},
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
