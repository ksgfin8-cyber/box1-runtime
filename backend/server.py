from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from layer1.adapters.box1_adapter import call_box1
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Any
import uuid
from datetime import datetime, timezone

# --------------------------------------------------
# Environment
# --------------------------------------------------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# --------------------------------------------------
# MongoDB
# --------------------------------------------------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# --------------------------------------------------
# App & Router
# --------------------------------------------------
app = FastAPI()
api_router = APIRouter(prefix="/api")

# --------------------------------------------------
# Models (existing)
# --------------------------------------------------
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


# --------------------------------------------------
# NEW: Capture Input Model
# --------------------------------------------------
class CaptureInput(BaseModel):
    raw_input: Any
    source_tag: str = "unknown"


# --------------------------------------------------
# Routes
# --------------------------------------------------
@api_router.get("/")
async def root():
    return {"message": "Hello World"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.model_dump())
    doc = status_obj.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check["timestamp"], str):
            check["timestamp"] = datetime.fromisoformat(check["timestamp"])
    return status_checks


# --------------------------------------------------
# 🔑 BOX 1 CAPTURE ENDPOINT (THE CORE)
# --------------------------------------------------
@api_router.post("/capture")
async def capture_signal(input: CaptureInput):
    # 1. Call adapter (server → adapter → box)
    signal = call_box1(
        raw_input=input.raw_input,
        source_tag=input.source_tag
    )

    # 2. Persist verbatim (NO mutation)
    await db.box1_signals.insert_one(signal)

    # 3. Return CanonicalSignal exactly
    return signal


# --------------------------------------------------
# Wiring
# --------------------------------------------------
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
