from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.config import get_settings
from app.database import DatabaseClient
from app.llm import SQLGenerator
from app.memory import count_memories, create_agent_memory
from app.models import ChatRequest, ChatResponse, HealthResponse
from app.pipeline import NL2SQLPipeline
from app.schema import load_database_schema
from app.security import SQLValidator
from app.seed_memory import seed_agent_memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    database = DatabaseClient(settings.db_path)
    schema = load_database_schema(settings.db_path)
    agent_memory = create_agent_memory(settings)
    await seed_agent_memory(agent_memory)

    app.state.settings = settings
    app.state.database = database
    app.state.agent_memory = agent_memory
    app.state.pipeline = NL2SQLPipeline(
        settings=settings,
        database=database,
        sql_generator=SQLGenerator(settings=settings, schema=schema),
        sql_validator=SQLValidator(schema=schema, database=database),
        agent_memory=agent_memory,
    )
    yield


app = FastAPI(title="NL2SQL API", lifespan=lifespan)

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Mount static asset directory for CSS and JS
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_ui():
    """Serve the Glassmorphism Front End"""
    return FileResponse("static/index.html")

@app.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    database_status = "connected" if request.app.state.database.check_connection() else "disconnected"
    return HealthResponse(
        status="ok",
        database=database_status,
        agent_memory_items=count_memories(request.app.state.agent_memory),
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    return await request.app.state.pipeline.run(payload.question)
