"""
Script to load dummy data into the database.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Brand, Campaign, Post, Platform, CampaignStatus
from datetime import datetime, timedelta
import uuid
import pytz


# Fixed UUIDs for consistent dummy data
DUMMY_BRAND_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DUMMY_CAMPAIGN_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
DUMMY_POST_IDS = [
    uuid.UUID("33333333-3333-3333-3333-333333333333"),
    uuid.UUID("44444444-4444-4444-4444-444444444444"),
    uuid.UUID("55555555-5555-5555-5555-555555555555"),
]


async def load_dummy_data(db: AsyncSession):
    """
    Load dummy data into the database if it doesn't already exist.
    
    Args:
        db: Database session
    """
    # Check if brand already exists
    brand_result = await db.execute(
        select(Brand).where(Brand.brand_id == DUMMY_BRAND_ID)
    )
    existing_brand = brand_result.scalar_one_or_none()
    
    if existing_brand is None:
        # Create brand
        brand = Brand(
            brand_id=DUMMY_BRAND_ID,
            brand_name="Demo Brand",
            brand_default_timezone="America/Los_Angeles",
            tone_profile="Professional and friendly"
        )
        db.add(brand)
        await db.commit()
        print("✓ Created dummy brand")
    else:
        print("✓ Dummy brand already exists")
    
    # Check if campaign already exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.campaign_id == DUMMY_CAMPAIGN_ID)
    )
    existing_campaign = campaign_result.scalar_one_or_none()
    
    if existing_campaign is None:
        # Create campaign (7 days from now)
        now = datetime.now(pytz.timezone("America/Los_Angeles"))
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = (start_date + timedelta(days=6)).replace(hour=23, minute=59, second=59)
        
        campaign = Campaign(
            campaign_id=DUMMY_CAMPAIGN_ID,
            brand_id=DUMMY_BRAND_ID,
            name="Summer Campaign 2024",
            goal="Increase brand awareness and engagement",
            start_date=start_date,
            end_date=end_date,
            status=CampaignStatus.DRAFT,
            created_at=now,
            updated_at=now
        )
        db.add(campaign)
        await db.commit()
        print("✓ Created dummy campaign")
    else:
        print("✓ Dummy campaign already exists")
    
    # Check and create posts
    created_posts = 0
    for i, post_id in enumerate(DUMMY_POST_IDS):
        post_result = await db.execute(
            select(Post).where(Post.post_id == post_id)
        )
        existing_post = post_result.scalar_one_or_none()
        
        if existing_post is None:
            now = datetime.now(pytz.UTC)
            post = Post(
                post_id=post_id,
                brand_id=DUMMY_BRAND_ID,
                campaign_id=DUMMY_CAMPAIGN_ID,
                title=f"Campaign Post {i + 1}",
                s3_url=f"s3://bucket/posts/post_{i + 1}.jpg",
                platform=Platform.TWITTER,
                created_at=now,
                updated_at=now
            )
            db.add(post)
            created_posts += 1
    
    if created_posts > 0:
        await db.commit()
        print(f"✓ Created {created_posts} dummy posts")
    else:
        print("✓ All dummy posts already exist")
    
    print("✓ Dummy data loading complete")

