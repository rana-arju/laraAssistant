import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import json

from app.main import app
from app.services.auth_service import auth_service


client = TestClient(app)


class TestAuthentication:
    """Test authentication middleware and JWT verification"""
    
    @pytest.fixture
    def mock_auth_response(self):
        """Mock successful auth response from Node.js backend"""
        return {
            "statusCode": 200,
            "message": "Token verified",
            "data": {
                "userId": "test-user-123",
                "email": "test@example.com",
                "firstName": "Test",
                "lastName": "User"
            }
        }
    
    @pytest.fixture  
    def mock_subscription_response(self):
        """Mock successful subscription response"""
        return {
            "statusCode": 200,
            "message": "Subscription valid",
            "data": {
                "planType": "premium",
                "expiresAt": "2024-12-31T23:59:59Z",
                "features": ["ai_chat", "voice_chat", "scheduling"]
            }
        }

    @patch('httpx.AsyncClient.post')
    async def test_valid_jwt_token(self, mock_post, mock_auth_response):
        """Test successful JWT token verification"""
        # Mock the HTTP response from Node.js auth service
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_auth_response
        mock_post.return_value = mock_response
        
        # Test the auth service directly
        result = await auth_service.verify_jwt_token("valid-token-123")
        
        assert result is not None
        assert result["userId"] == "test-user-123"
        assert result["email"] == "test@example.com"
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "Bearer valid-token-123" in str(call_args)

    @patch('httpx.AsyncClient.post')
    async def test_invalid_jwt_token(self, mock_post):
        """Test invalid JWT token handling"""
        # Mock 401 response for invalid token
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        result = await auth_service.verify_jwt_token("invalid-token")
        
        assert result is None

    @patch('httpx.AsyncClient.post')
    async def test_auth_service_network_error(self, mock_post):
        """Test auth service network error handling"""
        import httpx
        mock_post.side_effect = httpx.RequestError("Connection failed")
        
        result = await auth_service.verify_jwt_token("any-token")
        
        assert result is None

    def test_missing_authorization_header(self):
        """Test API request without Authorization header"""
        response = client.post("/api/v1/ai/chat/text", json={"message": "Hello"})
        
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["statusCode"] == 401
        assert "Authorization" in response_data["message"]

    @patch('app.services.auth_service.auth_service.get_current_user')
    def test_expired_token_response_format(self, mock_get_user):
        """Test response format for expired/invalid tokens"""
        mock_get_user.return_value = None
        
        response = client.post(
            "/api/v1/ai/chat/text",
            headers={"Authorization": "Bearer expired-token"},
            json={"message": "Hello"}
        )
        
        assert response.status_code == 401
        response_data = response.json()
        
        # Verify response follows sendResponse format
        assert "statusCode" in response_data
        assert "message" in response_data
        assert "data" in response_data
        assert response_data["statusCode"] == 401

    @patch('httpx.AsyncClient.post')
    async def test_subscription_verification(self, mock_post, mock_subscription_response):
        """Test subscription verification for features"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_subscription_response
        mock_post.return_value = mock_response
        
        result = await auth_service.verify_user_subscription("test-user-123", "ai_chat")
        
        assert result is not None
        assert result["planType"] == "premium"
        
        # Verify request body
        call_args = mock_post.call_args
        request_body = call_args.kwargs.get("json") or call_args[1].get("json")
        assert request_body["userId"] == "test-user-123"
        assert request_body["feature"] == "ai_chat"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])