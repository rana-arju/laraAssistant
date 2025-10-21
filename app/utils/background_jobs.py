import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, Any
import redis.asyncio as redis
from dramatiq import set_broker
from dramatiq.brokers.redis import RedisBroker
from dramatiq import actor

from app.models.scheduled_post import ScheduledPost, PostStatus
from app.models.scheduled_email import ScheduledEmail, EmailStatus
from app.models.notification import Notification, NotificationType


# Initialize Redis broker for Dramatiq
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
broker = RedisBroker(url=redis_url)
set_broker(broker)


class BackgroundJobService:
    """Service for managing background jobs and scheduled tasks"""
    
    def __init__(self):
        self.redis_client = redis.from_url(redis_url)
    
    async def queue_scheduled_post(self, post_id: str, scheduled_at: datetime):
        """Queue a social media post for publishing"""
        delay = (scheduled_at - datetime.now(timezone.utc)).total_seconds()
        if delay > 0:
            publish_social_post.send_with_options(
                args=[post_id],
                delay=int(delay * 1000)  # Dramatiq expects milliseconds
            )
    
    async def queue_scheduled_email(self, email_id: str, scheduled_at: datetime):
        """Queue an email for sending"""
        delay = (scheduled_at - datetime.now(timezone.utc)).total_seconds()
        if delay > 0:
            send_scheduled_email.send_with_options(
                args=[email_id],
                delay=int(delay * 1000)  # Dramatiq expects milliseconds
            )
    
    async def cancel_scheduled_job(self, job_id: str):
        """Cancel a scheduled job"""
        # TODO: Implement job cancellation logic
        pass


@actor
def publish_social_post(post_id: str):
    """Background job to publish social media post"""
    asyncio.run(_publish_social_post_async(post_id))


async def _publish_social_post_async(post_id: str):
    """Async implementation of social media post publishing"""
    try:
        # Find the scheduled post
        post = await ScheduledPost.get(post_id)
        if not post:
            print(f"Scheduled post {post_id} not found")
            return
        
        if post.status != PostStatus.SCHEDULED:
            print(f"Post {post_id} is not in scheduled status: {post.status}")
            return
        
        # Update status to processing
        post.status = PostStatus.PROCESSING
        post.attempts += 1
        post.lastAttemptAt = datetime.now(timezone.utc)
        await post.save()
        
        # TODO: Implement actual social media publishing logic
        # This would integrate with platform APIs (Twitter, Facebook, etc.)
        
        # For now, simulate publishing
        await asyncio.sleep(2)  # Simulate API call
        success = True  # Replace with actual API result
        
        if success:
            post.status = PostStatus.PUBLISHED
            post.publishedAt = datetime.now(timezone.utc)
            post.platformPostId = "mock-post-id-123"  # Replace with actual post ID
            
            # Create success notification
            notification = Notification(
                userId=post.userId,
                title="Post Published Successfully",
                message=f"Your {post.platform.value} post has been published successfully.",
                type=NotificationType.SUCCESS,
                category="scheduling",
                relatedEntityType="scheduled_post",
                relatedEntityId=post_id
            )
            await notification.insert()
            
        else:
            post.status = PostStatus.FAILED
            post.errorMessage = "Failed to publish to social media platform"
            
            # Create error notification
            notification = Notification(
                userId=post.userId,
                title="Post Publishing Failed",
                message=f"Failed to publish your {post.platform.value} post. Please try again.",
                type=NotificationType.ERROR,
                category="scheduling",
                relatedEntityType="scheduled_post",
                relatedEntityId=post_id
            )
            await notification.insert()
        
        post.updatedAt = datetime.now(timezone.utc)
        await post.save()
        
    except Exception as e:
        print(f"Error publishing social post {post_id}: {e}")
        
        # Update post status to failed
        try:
            post = await ScheduledPost.get(post_id)
            if post:
                post.status = PostStatus.FAILED
                post.errorMessage = str(e)
                post.updatedAt = datetime.now(timezone.utc)
                await post.save()
        except Exception as save_error:
            print(f"Error updating failed post status: {save_error}")


@actor
def send_scheduled_email(email_id: str):
    """Background job to send scheduled email"""
    asyncio.run(_send_scheduled_email_async(email_id))


async def _send_scheduled_email_async(email_id: str):
    """Async implementation of email sending"""
    try:
        # Find the scheduled email
        email = await ScheduledEmail.get(email_id)
        if not email:
            print(f"Scheduled email {email_id} not found")
            return
        
        if email.status != EmailStatus.SCHEDULED:
            print(f"Email {email_id} is not in scheduled status: {email.status}")
            return
        
        # Update status to processing
        email.status = EmailStatus.PROCESSING
        email.attempts += 1
        email.lastAttemptAt = datetime.now(timezone.utc)
        await email.save()
        
        # TODO: Implement actual email sending logic
        # This would integrate with email service providers (SendGrid, AWS SES, etc.)
        
        # For now, simulate email sending
        await asyncio.sleep(1)  # Simulate API call
        success = True  # Replace with actual API result
        
        if success:
            email.status = EmailStatus.SENT
            email.sentAt = datetime.now(timezone.utc)
            email.emailServiceId = "mock-email-id-456"  # Replace with actual service ID
            
            # Create success notification
            notification = Notification(
                userId=email.userId,
                title="Email Sent Successfully",
                message=f"Your email '{email.subject}' has been sent successfully.",
                type=NotificationType.SUCCESS,
                category="scheduling",
                relatedEntityType="scheduled_email",
                relatedEntityId=email_id
            )
            await notification.insert()
            
        else:
            email.status = EmailStatus.FAILED
            email.errorMessage = "Failed to send email"
            
            # Create error notification
            notification = Notification(
                userId=email.userId,
                title="Email Sending Failed",
                message=f"Failed to send your email '{email.subject}'. Please try again.",
                type=NotificationType.ERROR,
                category="scheduling",
                relatedEntityType="scheduled_email",
                relatedEntityId=email_id
            )
            await notification.insert()
        
        email.updatedAt = datetime.now(timezone.utc)
        await email.save()
        
    except Exception as e:
        print(f"Error sending email {email_id}: {e}")
        
        # Update email status to failed
        try:
            email = await ScheduledEmail.get(email_id)
            if email:
                email.status = EmailStatus.FAILED
                email.errorMessage = str(e)
                email.updatedAt = datetime.now(timezone.utc)
                await email.save()
        except Exception as save_error:
            print(f"Error updating failed email status: {save_error}")


@actor
def process_pending_notifications():
    """Process and send pending notifications"""
    asyncio.run(_process_pending_notifications_async())


async def _process_pending_notifications_async():
    """Process pending notifications that need to be sent"""
    try:
        # Find notifications that are scheduled to be sent
        now = datetime.now(timezone.utc)
        pending_notifications = await Notification.find({
            "status": "unread",
            "scheduledAt": {"$lte": now},
            "sentAt": None
        }).to_list()
        
        for notification in pending_notifications:
            try:
                # Mark as sent
                notification.sentAt = now
                notification.updatedAt = now
                await notification.save()
                
                # TODO: Send actual notifications via email, push, SMS, etc.
                # based on notification.channel
                
                print(f"Sent notification: {notification.title} to user {notification.userId}")
                
            except Exception as e:
                print(f"Error sending notification {notification.id}: {e}")
                
    except Exception as e:
        print(f"Error processing pending notifications: {e}")


# Global background job service instance
background_service = BackgroundJobService()


# CLI command to start the worker
if __name__ == "__main__":
    import dramatiq.cli
    import sys
    
    # Set up worker to process jobs
    sys.argv = ["dramatiq", "app.utils.background_jobs"]
    dramatiq.cli.main()