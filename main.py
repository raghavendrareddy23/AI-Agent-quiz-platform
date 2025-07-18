from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

import uvicorn
from app.services.ai_agent_service import AIAgentService
from app.models.database import Base, engine
from app.controllers import auth_controller, quiz_controller, ai_agent_controller
from fastapi.middleware.cors import CORSMiddleware
from app.utils.migrate import run_migrations
from config import settings

# run_migrations(apply_only=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting AI Agent...")
    agent = AIAgentService()
    app.state.quiz_agent = agent
    asyncio.create_task(agent.run_scheduled_generation())
    yield
    print("Stopping AI Agent...")
    await agent.stop()

app = FastAPI(
    title="AI Agent Quiz Platform",
    description="Platform for AI-generated and user-created quizzes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Create database tables
Base.metadata.create_all(bind=engine)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_controller.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(quiz_controller.router, prefix="/api/v1/quiz", tags=["quizzes"])
app.include_router(ai_agent_controller.router, prefix="/api/v1/ai", tags=["agents"])


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    port = settings.PORT
    uvicorn.run("main:app", host="0.0.0.0", port=port)

