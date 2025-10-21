import httpx
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.utils.response import send_error


class AuthService:
    """Service to verify JWT tokens with Node.js authentication backend"""
    
    def __init__(self):
        # TODO: Configure this URL in environment variables
        self.node_auth_url = os.getenv("NODE_AUTH_URL", "http://localhost:3000")
        self.verify_endpoint = f"{self.node_auth_url}/auth/verify"
        self.subscription_endpoint = f"{self.node_auth_url}/subscriptions/verify"
    
    async def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token with Node.js auth service
        
        Returns user data if valid, None if invalid
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.verify_endpoint,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Assuming Node backend returns: { statusCode: 200, message: "...", data: { user } }
                    if result.get("statusCode") == 200 and result.get("data"):
                        return result["data"]
                    return None
                else:
                    return None
                    
        except httpx.RequestError as e:
            print(f"Auth service request failed: {e}")
            return None
        except Exception as e:
            print(f"Auth service error: {e}")
            return None
    
    async def verify_user_subscription(self, user_id: str, feature: str = "ai_chat") -> Optional[Dict[str, Any]]:
        """
        Verify user subscription for specific feature
        
        Args:
            user_id: User ID to check subscription for
            feature: Feature to verify access for (ai_chat, voice_chat, scheduling)
            
        Returns subscription data if valid, None if invalid
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.subscription_endpoint,
                    json={
                        "userId": user_id,
                        "feature": feature
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("statusCode") == 200 and result.get("data"):
                        return result["data"]
                    return None
                else:
                    return None
                    
        except httpx.RequestError as e:
            print(f"Subscription service request failed: {e}")
            return None
        except Exception as e:
            print(f"Subscription service error: {e}")
            return None
    
    async def get_current_user(self, authorization_header: str) -> Optional[Dict[str, Any]]:
        """
        Extract and verify user from Authorization header
        
        Args:
            authorization_header: Full Authorization header value
            
        Returns user data if valid, None if invalid
        """
        if not authorization_header or not authorization_header.startswith("Bearer "):
            return None
            
        token = authorization_header.replace("Bearer ", "").strip()
        if not token:
            return None
            
        return await self.verify_jwt_token(token)


# Global auth service instance
auth_service = AuthService()