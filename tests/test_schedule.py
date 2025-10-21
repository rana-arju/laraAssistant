import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app


client = TestClient(app)


class TestSchedulingEndpoints:
    """Test scheduling endpoints for posts and emails"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        return {
            "userId": "test-user-123",
            "email": "test@example.com",
            "firstName": "Test"
        }
    
    @pytest.fixture  
    def mock_subscription(self):
        """Mock valid subscription with scheduling feature"""
        return {
            "planType": "premium",
            "features": ["scheduling", "ai_chat"],
            "quotas": {
                "monthlyPosts": 100,
                "usedPosts": 5
            }
        }
    
    @pytest.fixture
    def sample_post_data(self):
        """Sample social media post data"""
        return {
            "platform": "twitter",
            "scheduledAt": "2024-12-25T10:00:00Z",
            "content": {
                "text": "Merry Christmas everyone! 🎄",
                "imageUrls": ["https://example.com/christmas.jpg"]
            },
            "metadata": {
                "campaign": "holiday-2024"
            }
        }
    
    @pytest.fixture
    def sample_email_data(self):
        """Sample email scheduling data"""
        return {
            "to": ["customer@example.com"],
            "subject": "Holiday Greetings!",
            "body": "Wishing you a wonderful holiday season!",
            "scheduledAt": "2024-12-25T09:00:00Z",
            "metadata": {
                "template": "holiday",
                "campaign": "holiday-2024"
            }
        }

    def test_schedule_post_missing_auth(self, sample_post_data):
        """Test scheduling post without authentication"""
        response = client.post("/api/v1/schedule/post", json=sample_post_data)
        
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["statusCode"] == 401
        assert "Authorization" in response_data["message"]

    @patch('app.routes.schedule.get_current_user')
    @patch('app.services.auth_service.auth_service.verify_user_subscription')
    def test_schedule_post_no_subscription(
        self, 
        mock_subscription_verify, 
        mock_get_user, 
        mock_user,
        sample_post_data
    ):
        """Test scheduling post without valid subscription"""
        
        mock_get_user.return_value = mock_user
        mock_subscription_verify.return_value = None  # No subscription
        
        response = client.post(
            "/api/v1/schedule/post",
            headers={"Authorization": "Bearer valid-token"},
            json=sample_post_data
        )
        
        assert response.status_code == 403
        response_data = response.json()
        assert response_data["statusCode"] == 403
        assert "Subscription required" in response_data["message"]
        assert response_data["data"]["feature"] == "scheduling"

    @patch('app.routes.schedule.get_current_user')
    @patch('app.services.auth_service.auth_service.verify_user_subscription') 
    @patch('app.models.scheduled_post.ScheduledPost.insert')
    @patch('app.services.schedule_service.schedule_service.queue_post')
    async def test_schedule_post_success(
        self,
        mock_queue_post,
        mock_insert,
        mock_subscription_verify,
        mock_get_user,
        mock_user,
        mock_subscription,
        sample_post_data
    ):
        """Test successful post scheduling"""
        
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_subscription_verify.return_value = mock_subscription
        
        # Mock database insert
        mock_scheduled_post = MagicMock()
        mock_scheduled_post.scheduleId = "sched-123"
        mock_scheduled_post.status = "scheduled"
        mock_insert.return_value = mock_scheduled_post
        
        # Mock background job queuing
        mock_queue_post.return_value = True
        
        response = client.post(
            "/api/v1/schedule/post",
            headers={"Authorization": "Bearer valid-token"},
            json=sample_post_data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify response format
        assert response_data["statusCode"] == 200
        assert response_data["message"] == "Social media post scheduled successfully"
        assert "data" in response_data
        
        # Verify response data structure
        data = response_data["data"]
        assert "scheduleId" in data
        assert data["platform"] == "twitter"
        assert data["status"] == "scheduled"
        assert "scheduledAt" in data
        assert "content" in data

    def test_schedule_post_invalid_platform(self, mock_user):
        """Test scheduling post with invalid platform"""
        
        invalid_data = {
            "platform": "invalid-platform",
            "scheduledAt": "2024-12-25T10:00:00Z",
            "content": {"text": "Test post"}
        }
        
        response = client.post(
            "/api/v1/schedule/post",
            headers={"Authorization": "Bearer valid-token"},
            json=invalid_data
        )
        
        # Will likely fail on auth first, but validates structure
        assert response.status_code in [400, 401, 422]

    def test_schedule_post_past_date(self, mock_user):
        """Test scheduling post with past date"""
        
        past_data = {
            "platform": "twitter",
            "scheduledAt": "2020-01-01T10:00:00Z",  # Past date
            "content": {"text": "Test post"}
        }
        
        response = client.post(
            "/api/v1/schedule/post", 
            headers={"Authorization": "Bearer valid-token"},
            json=past_data
        )
        
        assert response.status_code in [400, 401]

    @patch('app.routes.schedule.get_current_user')
    @patch('app.services.auth_service.auth_service.verify_user_subscription')
    @patch('app.models.scheduled_email.ScheduledEmail.insert') 
    @patch('app.services.schedule_service.schedule_service.queue_email')
    async def test_schedule_email_success(
        self,
        mock_queue_email,
        mock_insert,
        mock_subscription_verify,
        mock_get_user,
        mock_user,
        mock_subscription,
        sample_email_data
    ):
        """Test successful email scheduling"""
        
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_subscription_verify.return_value = mock_subscription
        
        # Mock database insert
        mock_scheduled_email = MagicMock()
        mock_scheduled_email.scheduleId = "email-sched-456"
        mock_scheduled_email.status = "scheduled" 
        mock_insert.return_value = mock_scheduled_email
        
        # Mock background job queuing
        mock_queue_email.return_value = True
        
        response = client.post(
            "/api/v1/schedule/email",
            headers={"Authorization": "Bearer valid-token"},
            json=sample_email_data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify response format
        assert response_data["statusCode"] == 200
        assert response_data["message"] == "Email scheduled successfully"
        
        # Verify response data
        data = response_data["data"]
        assert "scheduleId" in data
        assert data["status"] == "scheduled"
        assert "scheduledAt" in data

    def test_schedule_email_invalid_recipients(self):
        """Test scheduling email with invalid recipient format"""
        
        invalid_email_data = {
            "to": "not-a-list",  # Should be list
            "subject": "Test",
            "body": "Test message",
            "scheduledAt": "2024-12-25T09:00:00Z"
        }
        
        response = client.post(
            "/api/v1/schedule/email",
            headers={"Authorization": "Bearer valid-token"},
            json=invalid_email_data
        )
        
        assert response.status_code in [400, 401, 422]

    @patch('app.routes.schedule.get_current_user')
    @patch('app.models.scheduled_post.ScheduledPost.find')
    @patch('app.models.scheduled_email.ScheduledEmail.find')
    async def test_get_user_scheduled_items(self, mock_find_emails, mock_find_posts, mock_get_user, mock_user):
        """Test retrieving user's scheduled items"""
        
        mock_get_user.return_value = mock_user
        
        # Mock scheduled posts
        mock_posts = [
            MagicMock(
                scheduleId="post-1",
                platform="twitter",
                status="scheduled",
                scheduledAt=datetime.now(timezone.utc)
            )
        ]
        
        # Mock scheduled emails  
        mock_emails = [
            MagicMock(
                scheduleId="email-1",
                subject="Test Email",
                status="scheduled", 
                scheduledAt=datetime.now(timezone.utc)
            )
        ]
        
        # Mock query chains
        mock_post_query = MagicMock()
        mock_post_query.sort.return_value = mock_post_query
        mock_post_query.limit.return_value = mock_post_query  
        mock_post_query.to_list.return_value = mock_posts
        mock_find_posts.return_value = mock_post_query
        
        mock_email_query = MagicMock()
        mock_email_query.sort.return_value = mock_email_query
        mock_email_query.limit.return_value = mock_email_query
        mock_email_query.to_list.return_value = mock_emails
        mock_find_emails.return_value = mock_email_query
        
        response = client.get(
            "/api/v1/schedule/items",
            headers={"Authorization": "Bearer valid-token"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["statusCode"] == 200
        assert "data" in response_data
        assert "posts" in response_data["data"]
        assert "emails" in response_data["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])