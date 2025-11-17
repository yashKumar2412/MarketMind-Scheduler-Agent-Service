from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

Base = declarative_base()


class ScheduleStatus(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Platform(enum.Enum):
    TWITTER = "TWITTER"
    YOUTUBE = "YOUTUBE"
    INSTAGRAM = "INSTAGRAM"
    LINKEDIN = "LINKEDIN"
    REDDIT = "REDDIT"
    TIKTOK = "TIKTOK"

class CampaignStatus(enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Schedule(Base):
    __tablename__ = "schedules"

    schedule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.post_id"), nullable=False)
    publish_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(ScheduleStatus), nullable=False, default=ScheduleStatus.PENDING)
    retry_count = Column(Integer, nullable=False, default=0)

class Post(Base):
    __tablename__ = "posts"

    post_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.brand_id"), nullable=False)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.campaign_id"), nullable=False)
    title = Column(String, nullable=False)
    s3_url = Column(String, nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

class Campaign(Base):
    __tablename__ = "campaigns"

    campaign_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.brand_id"), nullable=False)
    name = Column(String, nullable=False)
    goal = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

class Brand(Base):
    __tablename__ = "brands"

    brand_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_name = Column(String, nullable=False)
    brand_default_timezone = Column(String, nullable=False, default="UTC")
    tone_profile = Column(String, nullable=False)