from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import os
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, init_db, clear_db, AsyncSessionLocal
from service import ScheduleService
from load_dummy_data import load_dummy_data

app = FastAPI(
    title="Marketmind Scheduler Agent Service",
    description="API service for scheduling campaigns and posts",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Clear tables, initialize database and load dummy data on startup"""
    try:
        # Clear all existing tables
        await clear_db()
        print("✓ All tables cleared")
        
        # Initialize database tables
        await init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ ERROR: Failed to connect to database: {e}")
        print("  Please ensure PostgreSQL is running and DATABASE_URL is correct.")
        print(f"  Current DATABASE_URL: {os.getenv('DATABASE_URL', 'postgresql+asyncpg://user:password@localhost:5432/scheduler_db')}")
        raise  # Re-raise to prevent service from starting without DB
    
    # Load dummy data
    async with AsyncSessionLocal() as session:
        try:
            await load_dummy_data(session)
        except Exception as e:
            print(f"Warning: Failed to load dummy data: {e}")


class ScheduleItem(BaseModel):
    schedule_id: str
    post_id: str
    publish_time: str


class ScheduleResponse(BaseModel):
    schedule_id: str
    post_id: str
    publish_time: str
    status: str
    retry_count: int
    
    @classmethod
    def from_schedule(cls, schedule):
        """Convert Schedule model to ScheduleResponse"""
        return cls(
            schedule_id=str(schedule.schedule_id),
            post_id=str(schedule.post_id),
            publish_time=schedule.publish_time.isoformat(),
            status=schedule.status.value,
            retry_count=schedule.retry_count
        )


class CampaignScheduleResponse(BaseModel):
    campaign_id: str
    schedules: List[ScheduleResponse]


class PostScheduleRequest(BaseModel):
    timestamp: str = Field(
        ...,
        description="Timestamp in ISO format (e.g., '2025-11-17T19:00:00' or '2025-11-17T19:00:00Z')",
        example="2025-11-17T19:00:00"
    )
    timezone: Optional[str] = Field(
        None,
        description="Timezone string (e.g., 'America/Los_Angeles', 'PST', 'UTC'). If not provided, uses brand's default timezone.",
        example="America/Los_Angeles"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-17T19:00:00",
                "timezone": "America/Los_Angeles"
            }
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Marketmind Scheduler Agent Service",
        "status": "running",
        "endpoints": {
            "schedule_campaign": "/schedule/{campaign_id}",
            "schedule_post": "/schedule/{post_id}"
        }
    }


@app.post("/schedule/campaign/{campaign_id}")
async def schedule_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule a campaign by campaign_id
    
    Args:
        campaign_id: The unique identifier for the campaign
        db: Database session
    
    Returns:
        CampaignScheduleResponse with campaign_id and list of schedules
    """
    try:
        schedules = await ScheduleService.create_campaign_schedule(
            db=db,
            campaign_id=campaign_id
        )
        
        return CampaignScheduleResponse(
            campaign_id=campaign_id,
            schedules=[ScheduleResponse.from_schedule(schedule) for schedule in schedules]
        )
    except ValueError as e:
        # Handle not found or invalid UUID
        if "not found" in str(e).lower() or "no" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create campaign schedule: {str(e)}")


@app.post("/schedule/post/{post_id}")
async def schedule_post(
    post_id: str,
    request: PostScheduleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule a post by post_id
    
    Args:
        post_id: The unique identifier for the post
        request: Scheduling parameters with timestamp and timezone
        db: Database session
    
    Returns:
        ScheduleItem with schedule_id, post_id, and publish_time
    """
    try:
        schedule = await ScheduleService.create_post_schedule(
            db=db,
            post_id=post_id,
            timestamp=request.timestamp,
            timezone=request.timezone
        )
        
        return ScheduleItem(
            schedule_id=str(schedule.schedule_id),
            post_id=str(schedule.post_id),
            publish_time=schedule.publish_time.isoformat()
        )
    except ValueError as e:
        # Handle not found or invalid UUID
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@app.get("/schedule/campaign/{campaign_id}")
async def get_campaign_schedules(
    campaign_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all schedules for a campaign
    
    Args:
        campaign_id: The unique identifier for the campaign
        db: Database session
    
    Returns:
        CampaignScheduleResponse with campaign_id and list of schedules
    """
    try:
        schedules = await ScheduleService.get_campaign_schedules(
            db=db,
            campaign_id=campaign_id
        )
        
        return CampaignScheduleResponse(
            campaign_id=campaign_id,
            schedules=[ScheduleResponse.from_schedule(schedule) for schedule in schedules]
        )
    except ValueError as e:
        if "not found" in str(e).lower() or "no" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaign schedules: {str(e)}")


@app.get("/schedule/post/{post_id}")
async def get_post_schedule(
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the schedule for a post (returns the most recent schedule)
    
    Args:
        post_id: The unique identifier for the post
        db: Database session
    
    Returns:
        Single ScheduleResponse object for the post
    """
    try:
        schedule = await ScheduleService.get_post_schedule(
            db=db,
            post_id=post_id
        )
        
        return ScheduleResponse.from_schedule(schedule)
    except ValueError as e:
        if "not found" in str(e).lower() or "no schedule" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch post schedule: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}