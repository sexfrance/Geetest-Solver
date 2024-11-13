from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from async_solver import AsyncGeetestSolver

app = FastAPI(
    title="Geetest Solver API",
    description="API for solving Geetest v4 captchas",
    version="1.0.0"
)

class TaskRequest(BaseModel):
    sitekey: str
    url: Optional[str] = None

class TaskResponse(BaseModel):
    taskId: str
    status: str = "processing"

class ResultResponse(BaseModel):
    status: str
    solution: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


tasks = {}

@app.post("/task/create")
async def create_task(request: TaskRequest):
    import uuid
    task_id = str(uuid.uuid4())

    tasks[task_id] = {
        "status": "processing",
        "solution": None,
        "error": None
    }

    asyncio.create_task(solve_captcha(task_id, request.sitekey))
    return TaskResponse(taskId=task_id)

@app.get("/task/{task_id}")
async def get_task_result(task_id: str):

    task = tasks.get(task_id)
    if not task:
        return ResultResponse(
            status="error",
            error="Task not found"
        )

    return ResultResponse(
        status=task["status"],
        solution=task["solution"],
        error=task["error"]
    )

async def solve_captcha(task_id: str, sitekey: str):
    """Background task to solve the captcha"""
    try:
        solver = AsyncGeetestSolver(debug=False)
        result = await solver.solve(sitekey=sitekey)

        if result.status == "success":
            tasks[task_id].update({
                "status": "ready",
                "solution": {
                    "response": result.response,
                    "elapsed": result.elapsed_time_seconds
                }
            })
        else:
            tasks[task_id].update({
                "status": "failed",
                "error": result.reason
            })

    except Exception as e:
        tasks[task_id].update({
            "status": "failed",
            "error": str(e)
        })

@app.get("/")
async def read_root():
    return {
        "name": "Geetest Solver API",
        "version": "1.0.0",
        "status": "running"
    } 