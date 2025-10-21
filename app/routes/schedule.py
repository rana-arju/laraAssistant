from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone
import uuid

from app.utils.response import send_response, send_error
from app.services.auth_service import auth_service
from app.models.scheduled_post import ScheduledPost, SocialPlatform, PostContent
from app.models.scheduled_email import ScheduledEmail, EmailPriority


router = APIRouter()


# Request models
class PostContentRequest(BaseModel):
    text: str = Field(..., description="Post text content", max_length=2000)
    imageUrls: Optional[List[str]] = Field(default_factory=list, description="Image URLs")
    videoUrls: Optional[List[str]] = Field(default_factory=list, description="Video URLs")
    hashtags: Optional[List[str]] = Field(default_factory=list, description="Hashtags")
    mentions: Optional[List[str]] = Field(default_factory=list, description="User mentions")


class SchedulePostRequest(BaseModel):
    platform: SocialPlatform = Field(..., description="Target social media platform")
    scheduledAt: datetime = Field(..., description="When to publish the post")
    content: PostContentRequest = Field(..., description="Post content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('scheduledAt')
    def validate_scheduled_at(cls, v):
        if v <= datetime.now(timezone.utc):
            raise ValueError('Scheduled time must be in the future')
        return v


class ScheduleEmailRequest(BaseModel):
    to: List[str] = Field(..., description="Recipient email addresses", min_items=1)
    subject: str = Field(..., description="Email subject", max_length=200)
    body: str = Field(..., description="Email body content")
    scheduledAt: datetime = Field(..., description="When to send the email")
    cc: Optional[List[str]] = Field(default_factory=list, description="CC recipients")
    bcc: Optional[List[str]] = Field(default_factory=list, description="BCC recipients")
    priority: EmailPriority = Field(default=EmailPriority.NORMAL, description="Email priority")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('scheduledAt')
    def validate_scheduled_at(cls, v):
        if v <= datetime.now(timezone.utc):
            raise ValueError('Scheduled time must be in the future')
        return v


# Auth dependency
async def get_current_user(authorization: str = Depends(lambda: None)) -> Dict[str, Any]:
    """Extract current user from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    user = await auth_service.get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user


@router.post("/post")
async def schedule_social_media_post(
    request: SchedulePostRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Schedule a social media post
    
    Features:
    - Verify user authentication and subscription 
    - Validate post content and scheduling time
    - Store in database and queue for background processing
    - Track user's scheduling quota
    """
    try:
        user_id = current_user.get("userId") or current_user.get("id")
        if not user_id:
            return send_error(
                status_code=400,
                message="Invalid user data",
                data={"error": "User ID not found"}
            )
        
        # Verify subscription for scheduling feature
        subscription = await auth_service.verify_user_subscription(user_id, "scheduling")
        if not subscription:
            return send_error(
                status_code=403,
                message="Subscription required for scheduling",
                data={"feature": "scheduling", "required": True}
            )
        
        # Generate unique schedule ID
        schedule_id = str(uuid.uuid4())
        
        # Create post content
        post_content = PostContent(
            text=request.content.text,
            imageUrls=request.content.imageUrls,
            videoUrls=request.content.videoUrls,
            hashtags=request.content.hashtags,
            mentions=request.content.mentions
        )
        
        # Create scheduled post
        scheduled_post = ScheduledPost(
            scheduleId=schedule_id,
            userId=user_id,
            platform=request.platform,
            content=post_content,
            scheduledAt=request.scheduledAt,
            metadata=request.metadata
        )
        
        # Save to database
        await scheduled_post.insert()
        
        # TODO: Queue for background processing
        # await schedule_service.queue_post(scheduled_post)
        
        response_data = {
            "scheduleId": schedule_id,
            "platform": request.platform.value,
            "scheduledAt": request.scheduledAt.isoformat(),
            "status": "scheduled",
            "content": {
                "text": request.content.text,
                "imageUrls": request.content.imageUrls,
                "videoUrls": request.content.videoUrls,
                "hashtags": request.content.hashtags,
                "mentions": request.content.mentions
            }
        }
        
        return send_response(
            status_code=200,
            message="Social media post scheduled successfully",
            data=response_data
        )
        
    except ValueError as e:
        return send_error(
            status_code=400,
            message=str(e)
        )
    except Exception as e:
        print(f"Schedule post error: {e}")
        return send_error(
            status_code=500,
            message="Failed to schedule post"
        )


@router.post("/email") 
async def schedule_email(
    request: ScheduleEmailRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Schedule an email
    
    Features:
    - Verify user authentication and subscription
    - Validate email content and recipients
    - Store in database and queue for background processing
    - Track user's scheduling quota
    """
    try:
        user_id = current_user.get("userId") or current_user.get("id")
        if not user_id:
            return send_error(
                status_code=400,
                message="Invalid user data",
                data={"error": "User ID not found"}
            )
        
        # Verify subscription for scheduling feature
        subscription = await auth_service.verify_user_subscription(user_id, "scheduling")
        if not subscription:
            return send_error(
                status_code=403,
                message="Subscription required for scheduling",
                data={"feature": "scheduling", "required": True}
            )
        
        # Generate unique schedule ID
        schedule_id = str(uuid.uuid4())
        
        # Create scheduled email
        scheduled_email = ScheduledEmail(
            scheduleId=schedule_id,
            userId=user_id,
            to=request.to,
            cc=request.cc,
            bcc=request.bcc,
            subject=request.subject,
            body=request.body,
            scheduledAt=request.scheduledAt,
            priority=request.priority,
            metadata=request.metadata
        )
        
        # Save to database
        await scheduled_email.insert()
        
        # TODO: Queue for background processing
        # await schedule_service.queue_email(scheduled_email)
        
        response_data = {
            "scheduleId": schedule_id,
            "to": request.to,
            "subject": request.subject,
            "scheduledAt": request.scheduledAt.isoformat(),
            "priority": request.priority.value,
            "status": "scheduled"
        }
        
        return send_response(
            status_code=200,
            message="Email scheduled successfully",
            data=response_data
        )
        
    except ValueError as e:
        return send_error(
            status_code=400,
            message=str(e)
        )
    except Exception as e:
        print(f"Schedule email error: {e}")
        return send_error(
            status_code=500,
            message="Failed to schedule email"
        )


@router.get("/posts")
async def get_scheduled_posts(
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    platform: Optional[SocialPlatform] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's scheduled posts"""
    try:
        user_id = current_user.get("userId") or current_user.get("id")
        
        # Build query filters
        query_filters = {"userId": user_id}
        if status:
            query_filters["status"] = status
        if platform:
            query_filters["platform"] = platform
        
        # Get scheduled posts
        posts = await ScheduledPost.find(query_filters).sort([("scheduledAt", 1)]).limit(limit).to_list()
        
        posts_data = []
        for post in posts:
            posts_data.append({
                "scheduleId": post.scheduleId,
                "platform": post.platform.value,
                "content": {
                    "text": post.content.text,
                    "imageUrls": post.content.imageUrls,
                    "videoUrls": post.content.videoUrls,
                    "hashtags": post.content.hashtags,
                    "mentions": post.content.mentions
                },
                "scheduledAt": post.scheduledAt.isoformat(),
                "status": post.status.value,
                "createdAt": post.createdAt.isoformat(),
                "publishedAt": post.publishedAt.isoformat() if post.publishedAt else None
            })
        
        return send_response(
            status_code=200,
            message="Scheduled posts retrieved successfully",
            data={"posts": posts_data}
        )
        
    except Exception as e:
        print(f"Get scheduled posts error: {e}")
        return send_error(
            status_code=500,
            message="Failed to retrieve scheduled posts"
        )


@router.get("/emails")
async def get_scheduled_emails(
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's scheduled emails"""
    try:
        user_id = current_user.get("userId") or current_user.get("id")
        
        # Build query filters
        query_filters = {"userId": user_id}
        if status:
            query_filters["status"] = status
        
        # Get scheduled emails
        emails = await ScheduledEmail.find(query_filters).sort([("scheduledAt", 1)]).limit(limit).to_list()
        
        emails_data = []
        for email in emails:
            emails_data.append({
                "scheduleId": email.scheduleId,
                "to": email.to,
                "subject": email.subject,
                "scheduledAt": email.scheduledAt.isoformat(),
                "status": email.status.value,
                "priority": email.priority.value,
                "createdAt": email.createdAt.isoformat(),
                "sentAt": email.sentAt.isoformat() if email.sentAt else None
            })
        
        return send_response(
            status_code=200,
            message="Scheduled emails retrieved successfully",
            data={"emails": emails_data}
        )
        
    except Exception as e:
        print(f"Get scheduled emails error: {e}")
        return send_error(
            status_code=500,
            message="Failed to retrieve scheduled emails"
        )


@router.delete("/post/{schedule_id}")
async def cancel_scheduled_post(
    schedule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Cancel a scheduled post"""
    try:
        user_id = current_user.get("userId") or current_user.get("id")
        
        # Find the scheduled post
        post = await ScheduledPost.find_one({
            "scheduleId": schedule_id,
            "userId": user_id
        })
        
        if not post:
            return send_error(
                status_code=404,
                message="Scheduled post not found"
            )
        
        # Update status to cancelled
        post.status = "cancelled"
        post.updatedAt = datetime.now(timezone.utc)
        await post.save()
        
        return send_response(
            status_code=200,
            message="Scheduled post cancelled successfully",
            data={"scheduleId": schedule_id, "status": "cancelled"}
        )
        
    except Exception as e:
        print(f"Cancel post error: {e}")
        return send_error(
            status_code=500,
            message="Failed to cancel scheduled post"
        )


@router.delete("/email/{schedule_id}")
async def cancel_scheduled_email(
    schedule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Cancel a scheduled email"""
    try:
        user_id = current_user.get("userId") or current_user.get("id")
        
        # Find the scheduled email
        email = await ScheduledEmail.find_one({
            "scheduleId": schedule_id,
            "userId": user_id
        })
        
        if not email:
            return send_error(
                status_code=404,
                message="Scheduled email not found"
            )
        
        # Update status to cancelled
        email.status = "cancelled"
        email.updatedAt = datetime.now(timezone.utc)
        await email.save()
        
        return send_response(
            status_code=200,
            message="Scheduled email cancelled successfully",
            data={"scheduleId": schedule_id, "status": "cancelled"}
        )
        
    except Exception as e:
        print(f"Cancel email error: {e}")
        return send_error(
            status_code=500,
            message="Failed to cancel scheduled email"
        )