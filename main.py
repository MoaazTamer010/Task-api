from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn

# ============================================
# In-memory "database" - a list of tasks
# ============================================
tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Build CRUD API", "done": False},
    {"id": 3, "title": "Write README", "done": True},
]

next_id = 4


# ============================================
# Pydantic models for request/response validation
# ============================================
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Task title")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, description="Task title")
    done: Optional[bool] = Field(None, description="Task completion status")


class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool


# ============================================
# FastAPI app initialization
# ============================================
app = FastAPI(
    title="Task API",
    description="A simple CRUD API for managing a to-do list",
    version="1.0"
)


# ============================================
# Stage 1: Root & Health endpoints
# ============================================
@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


# ============================================
# Stage 2: Read endpoints (GET)
# ============================================
@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
async def get_all_tasks():
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found"
    )


# ============================================
# Stage 3: Create endpoint (POST)
# ============================================
@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"]
)
async def create_task(task: TaskCreate):
    global next_id
    
    if not task.title or not task.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty"
        )
    
    new_task = {
        "id": next_id,
        "title": task.title.strip(),
        "done": False
    }
    tasks.append(new_task)
    next_id += 1
    return new_task


# ============================================
# Stage 4: Update & Delete endpoints (PUT, DELETE)
# ============================================
@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def update_task(task_id: int, task_update: TaskUpdate):
    task_index = None
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            task_index = i
            break
    
    if task_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    if task_update.title is None and task_update.done is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field (title or done) must be provided"
        )
    
    if task_update.title is not None and not task_update.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty"
        )
    
    if task_update.title is not None:
        tasks[task_index]["title"] = task_update.title.strip()
    if task_update.done is not None:
        tasks[task_index]["done"] = task_update.done
    
    return tasks[task_index]


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
async def delete_task(task_id: int):
    task_index = None
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            task_index = i
            break
    
    if task_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    tasks.pop(task_index)
    return None


# ============================================
# Extras (optional stretch goals)
# ============================================
@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
async def get_all_tasks_with_filters(
    done: Optional[bool] = None,
    search: Optional[str] = None
):
    result = tasks
    
    if done is not None:
        result = [t for t in result if t["done"] == done]
    
    if search:
        search_lower = search.lower()
        result = [t for t in result if search_lower in t["title"].lower()]
    
    return result


@app.get("/stats", tags=["Stats"])
async def get_stats():
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    open_count = total - done
    return {
        "total": total,
        "done": done,
        "open": open_count
    }


@app.post("/reset", status_code=status.HTTP_200_OK, tags=["Admin"])
async def reset_tasks():
    global next_id, tasks
    tasks = [
        {"id": 1, "title": "Learn FastAPI", "done": False},
        {"id": 2, "title": "Build CRUD API", "done": False},
        {"id": 3, "title": "Write README", "done": True},
    ]
    next_id = 4
    return {"message": "Tasks reset to default", "tasks": tasks}


# ============================================
# Run the server
# ============================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
