from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from models import Schedule, ScheduleStatus, Post, Brand, Campaign, Platform
from datetime import datetime
import uuid
import pytz
from naive_scheduler import schedule_posts


class ScheduleService:
    """Service layer for schedule business logic"""

    @staticmethod
    async def create_post_schedule(
        db: AsyncSession,
        post_id: str,
        timestamp: str,
        timezone: str | None = None
    ) -> Schedule:
        """
        Create a post schedule by converting timestamp to UTC and saving to database
        
        Args:
            db: Database session
            post_id: The post identifier (UUID string)
            timestamp: Timestamp string in the specified timezone
            timezone: Optional timezone string (e.g., 'PST', 'UTC').
                     If not provided, uses brand's default timezone.
        
        Returns:
            Schedule object with generated schedule_id
        """
        # Convert post_id string to UUID
        post_uuid = uuid.UUID(post_id)
        
        # If timezone not provided, fetch from brand
        if timezone is None:
            # Fetch post to get brand_id
            post_result = await db.execute(
                select(Post).where(Post.post_id == post_uuid)
            )
            post = post_result.scalar_one_or_none()
            
            if post is None:
                raise ValueError(f"Post with id {post_id} not found")
            
            # Fetch brand to get default timezone
            brand_result = await db.execute(
                select(Brand).where(Brand.brand_id == post.brand_id)
            )
            brand = brand_result.scalar_one_or_none()
            
            if brand is None:
                raise ValueError(f"Brand with id {post.brand_id} not found")
            
            timezone = brand.brand_default_timezone
        
        # Parse the timestamp string (remove timezone info if present, we'll use the provided timezone)
        try:
            # Try parsing with timezone info first
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            # Remove timezone info - we'll use the provided timezone parameter
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
        except ValueError:
            # Parse without timezone info
            dt = datetime.fromisoformat(timestamp)
        
        # Localize to the specified timezone
        tz = pytz.timezone(timezone)
        dt = tz.localize(dt)
        
        # Convert to UTC
        publish_time_utc = dt.astimezone(pytz.UTC)
        
        # Generate UUID for schedule_id
        schedule_id = uuid.uuid4()
        
        # Create schedule record
        schedule = Schedule(
            schedule_id=schedule_id,
            post_id=post_uuid,
            publish_time=publish_time_utc,
            status=ScheduleStatus.PENDING,
            retry_count=0
        )
        
        # Save to database
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)
        
        return schedule

    @staticmethod
    async def create_campaign_schedule(
        db: AsyncSession,
        campaign_id: str
    ) -> list[Schedule]:
        """
        Create schedules for all posts in a campaign with smart scheduling
        
        Args:
            db: Database session
            campaign_id: The campaign identifier (UUID string)
        
        Returns:
            List of Schedule objects created for the campaign
        """
        # Convert campaign_id string to UUID
        campaign_uuid = uuid.UUID(campaign_id)
        
        # Fetch campaign info
        campaign_result = await db.execute(
            select(Campaign).where(Campaign.campaign_id == campaign_uuid)
        )
        campaign = campaign_result.scalar_one_or_none()
        
        if campaign is None:
            raise ValueError(f"Campaign with id {campaign_id} not found")
        
        # Fetch brand to get default timezone
        brand_result = await db.execute(
            select(Brand).where(Brand.brand_id == campaign.brand_id)
        )
        brand = brand_result.scalar_one_or_none()
        
        if brand is None:
            raise ValueError(f"Brand with id {campaign.brand_id} not found")
        
        # Get brand default timezone
        brand_timezone = brand.brand_default_timezone
        
        # Fetch posts for this campaign (hardcoded to TWITTER for now)
        posts_result = await db.execute(
            select(Post).where(
                Post.campaign_id == campaign_uuid,
                Post.platform == Platform.TWITTER
            )
        )
        posts = posts_result.scalars().all()
        
        if not posts:
            raise ValueError(f"No TWITTER posts found for campaign {campaign_id}")

        num_posts = len(posts)
        
        if num_posts == 0:
            raise ValueError(f"No posts to schedule for campaign {campaign_id}")
        
        # TODO: Replace naive_scheduler with agentic_scheduler for LLM-based intelligent scheduling
        # Generate publish times using naive scheduler (all at 7 PM)
        publish_times_utc = schedule_posts(
            num_posts=num_posts,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            timezone=brand_timezone
        )
        
        # Create schedules
        schedules = []
        for i, post in enumerate(posts):
            # Generate UUID for schedule_id
            schedule_id = uuid.uuid4()
            
            # Create schedule record
            schedule = Schedule(
                schedule_id=schedule_id,
                post_id=post.post_id,
                publish_time=publish_times_utc[i],
                status=ScheduleStatus.PENDING,
                retry_count=0
            )
            
            schedules.append(schedule)
            db.add(schedule)
        
        # Save all schedules to database
        await db.commit()
        
        # Refresh all schedules
        for schedule in schedules:
            await db.refresh(schedule)
        
        return schedules

    @staticmethod
    async def get_campaign_schedules(
        db: AsyncSession,
        campaign_id: str
    ) -> list[Schedule]:
        """
        Get all schedules for a campaign
        
        Args:
            db: Database session
            campaign_id: The campaign identifier (UUID string)
        
        Returns:
            List of Schedule objects for the campaign
        """
        campaign_uuid = uuid.UUID(campaign_id)
        
        # Fetch all posts for this campaign
        posts_result = await db.execute(
            select(Post).where(Post.campaign_id == campaign_uuid)
        )
        posts = posts_result.scalars().all()
        
        if not posts:
            raise ValueError(f"No posts found for campaign {campaign_id}")
        
        post_ids = [post.post_id for post in posts]
        
        # Fetch all schedules for these posts
        schedules_result = await db.execute(
            select(Schedule).where(Schedule.post_id.in_(post_ids))
        )
        schedules = schedules_result.scalars().all()
        
        return schedules

    @staticmethod
    async def get_post_schedule(
        db: AsyncSession,
        post_id: str
    ) -> Schedule:
        """
        Get the schedule for a post (returns the most recent schedule)
        
        Args:
            db: Database session
            post_id: The post identifier (UUID string)
        
        Returns:
            Schedule object for the post (most recent)
        """
        post_uuid = uuid.UUID(post_id)
        
        # Verify post exists
        post_result = await db.execute(
            select(Post).where(Post.post_id == post_uuid)
        )
        post = post_result.scalar_one_or_none()
        
        if post is None:
            raise ValueError(f"Post with id {post_id} not found")
        
        # Fetch the most recent schedule for this post (ordered by publish_time desc)
        schedule_result = await db.execute(
            select(Schedule)
            .where(Schedule.post_id == post_uuid)
            .order_by(desc(Schedule.publish_time))
            .limit(1)
        )
        schedule = schedule_result.scalar_one_or_none()
        
        if schedule is None:
            raise ValueError(f"No schedule found for post {post_id}")
        
        return schedule

