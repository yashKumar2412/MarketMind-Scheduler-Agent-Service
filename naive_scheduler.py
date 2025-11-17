"""
Naive scheduler for campaign posts.

TODO: Replace this with agentic_scheduler that uses LLM/agent for intelligent scheduling.
"""
from datetime import datetime, timedelta, time
import pytz


def schedule_posts(
    num_posts: int,
    start_date: datetime,
    end_date: datetime,
    timezone: str
) -> list[datetime]:
    """
    Schedule posts at 7 PM using naive distribution logic.
    
    Args:
        num_posts: Number of posts to schedule
        start_date: Campaign start date (in brand timezone)
        end_date: Campaign end date (in brand timezone)
        timezone: Brand timezone string
    
    Returns:
        List of publish times in UTC (all at 7 PM in brand timezone)
    
    Raises:
        ValueError: If num_posts exceeds number of days
    """
    tz = pytz.timezone(timezone)
    
    # If dates are timezone-naive, localize them to brand timezone
    start_date_local = start_date
    end_date_local = end_date
    if start_date_local.tzinfo is None:
        start_date_local = tz.localize(start_date_local)
    if end_date_local.tzinfo is None:
        end_date_local = tz.localize(end_date_local)
    
    # Calculate number of days (including start and end)
    num_days = (end_date_local.date() - start_date_local.date()).days + 1
    
    # Validate: throw error if more posts than days
    if num_posts > num_days:
        raise ValueError(
            f"Cannot schedule {num_posts} posts across {num_days} days. "
            f"Number of posts must not exceed number of days."
        )
    
    # Generate publish times: all at 7 PM
    publish_times_utc = []
    
    if num_posts == 1:
        # 1 post: first day at 7 PM
        first_day = start_date_local.date()
        publish_time_local = tz.localize(datetime.combine(first_day, time(hour=19, minute=0)))
        publish_times_utc.append(publish_time_local.astimezone(pytz.UTC))
    elif num_posts == 2:
        # 2 posts: first day and last day at 7 PM
        first_day = start_date_local.date()
        last_day = end_date_local.date()
        
        publish_time_first = tz.localize(datetime.combine(first_day, time(hour=19, minute=0)))
        publish_times_utc.append(publish_time_first.astimezone(pytz.UTC))
        
        publish_time_last = tz.localize(datetime.combine(last_day, time(hour=19, minute=0)))
        publish_times_utc.append(publish_time_last.astimezone(pytz.UTC))
    else:
        # More than 2 posts: first day, last day, and evenly distribute the rest
        first_day = start_date_local.date()
        last_day = end_date_local.date()
        
        # Remaining posts distributed evenly on days in between
        remaining_posts = num_posts - 2
        days_between = num_days - 2
        
        # Calculate which days to use for all posts
        if days_between > 0 and remaining_posts > 0:
            # Distribute remaining posts evenly across days in between
            if remaining_posts == 1:
                # Single post in the middle
                middle_day_offset = days_between // 2
                middle_day = first_day + timedelta(days=middle_day_offset + 1)
                days_to_use = [first_day, middle_day, last_day]
            else:
                # Multiple posts: distribute evenly
                # Calculate interval to space posts evenly
                interval = days_between / (remaining_posts + 1)
                days_to_use = [first_day]  # Start with first day
                
                # Add days in between
                for i in range(remaining_posts):
                    day_offset = int((i + 1) * interval)
                    current_day = first_day + timedelta(days=day_offset + 1)
                    days_to_use.append(current_day)
                
                days_to_use.append(last_day)  # End with last day
        else:
            # No days in between or no remaining posts
            days_to_use = [first_day, last_day]
        
        # Create publish times for all days at 7 PM
        for day in days_to_use:
            publish_time = tz.localize(datetime.combine(day, time(hour=19, minute=0)))
            publish_times_utc.append(publish_time.astimezone(pytz.UTC))
    
    return publish_times_utc
