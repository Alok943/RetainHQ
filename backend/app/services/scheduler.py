from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Activity, Review

def schedule_reviews_for_activity(activity: Activity) -> List[Review]:
    """
    Creates and returns scheduled reviews for a newly logged activity.
    Logic: If difficulty >= 4 OR needed_hint is True, create 4 reviews at +3, +7, +14, +30 days.
    (Note: The activity must be flushed/committed so it has an ID before passing it here).
    """
    reviews = []
    
    if activity.difficulty >= 4 or activity.needed_hint:
        intervals = [3, 7, 14, 30]
        now = datetime.utcnow()
        
        for days in intervals:
            review = Review(
                user_id=activity.user_id,
                activity_id=activity.id,
                status="due",
                scheduled_for=now + timedelta(days=days)
            )
            reviews.append(review)
            
    return reviews
