from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any
from pydantic import BaseModel
import uuid
import os
import tempfile
from datetime import datetime

from app.utils.response import send_response, send_error
from app.services.auth_service import auth_service
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service
from app.services.ai_service import ai_service
from app.models.ai_chat_log import AiChatLog


router = APIRouter()


# Request/Response models
class ChatTextRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    saveToMemory: bool = True


class ChatResponse(BaseModel):
    conversationId: str
    message: str
    responseText: str
    tokenUsage: Dict[str, int]
    memoryStored: bool


# Dependency for current user authentication
async def get_current_user(authorization: str = Depends(lambda: None)) -> Dict[str, Any]:
    """Extract current user from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    user = await auth_service.get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user


@router.post("/text")
async def chat_text(
    request: ChatTextRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process text chat message with AI
    
    Features:
    - Verify user authentication and subscription 
    - Generate embeddings and store in Qdrant
    - Retrieve relevant context from memory
    - Get AI response
    - Log interaction to MongoDB
    - Track token usage
    """
    try:
        user_id = current_user.get("userId") or current_user.get("id")
        if not user_id:
            return send_error(
                status_code=400,
                message="Invalid user data",
                data={"error": "User ID not found"}
            )
        
        # Verify subscription for AI chat feature
        subscription = await auth_service.verify_user_subscription(user_id, "ai_chat")
        if not subscription:
            return send_error(
                status_code=403,
                message="Subscription required for AI chat",
                data={"feature": "ai_chat", "required": True}
            )
        
        # Generate or use existing conversation ID
        conversation_id = request.conversationId or str(uuid.uuid4())
        
        # Generate embedding for user message
        user_embedding = await embedding_service.get_embedding(request.message)
        
        # Search for relevant context if memory storage is enabled
        context_memories = []
        if request.saveToMemory:
            context_memories = await qdrant_service.search_similar(
                query_embedding=user_embedding,
                user_id=user_id,
                limit=5,
                score_threshold=0.7,
                conversation_id=conversation_id
            )
        
        # Get conversation context
        conversation_context = await qdrant_service.get_conversation_context(
            user_id=user_id,
            conversation_id=conversation_id,
            limit=10
        )
        
        # Prepare context for AI
        context_text = ""
        if context_memories:
            context_text += "\\n\\nRelevant context from memory:\\n"
            for memory in context_memories:
                context_text += f"- {memory['payload']['text']}\\n"
        
        if conversation_context:
            context_text += "\\n\\nRecent conversation:\\n"
            for msg in conversation_context[-5:]:  # Last 5 messages
                context_text += f"- {msg['payload']['text']}\\n"
        
        # Get AI response
        ai_response = await ai_service.chat_completion(
            message=request.message,
            context=context_text,
            user_id=user_id
        )
        
        memory_stored = False
        # Store user message and AI response in Qdrant if enabled
        if request.saveToMemory:
            # Store user message
            await qdrant_service.store_embedding(
                user_id=user_id,
                text=request.message,
                embedding=user_embedding,
                conversation_id=conversation_id,
                source_type="user_message",
                metadata={
                    "role": "user",
                    **(request.metadata or {})
                }
            )
            
            # Store AI response
            ai_embedding = await embedding_service.get_embedding(ai_response["text"])
            await qdrant_service.store_embedding(
                user_id=user_id,
                text=ai_response["text"],
                embedding=ai_embedding,
                conversation_id=conversation_id,
                source_type="ai_response",
                metadata={"role": "assistant"}
            )
            memory_stored = True
        
        # Log interaction to MongoDB
        chat_log = AiChatLog(
            userId=user_id,
            conversationId=conversation_id,
            userMessage=request.message,
            aiResponse=ai_response["text"],
            tokenUsage=ai_response["token_usage"],
            model=ai_response.get("model", "unknown"),
            createdAt=datetime.utcnow(),
            metadata=request.metadata
        )
        await chat_log.insert()
        
        response_data = {
            "conversationId": conversation_id,
            "message": request.message,
            "responseText": ai_response["text"],
            "tokenUsage": ai_response["token_usage"],
            "memoryStored": memory_stored
        }
        
        return send_response(
            status_code=200,
            message="Chat completed successfully",
            data=response_data
        )
        
    except Exception as e:
        print(f"Chat error: {e}")
        return send_error(
            status_code=500,
            message="Failed to process chat",
            data={"error": str(e) if os.getenv("DEBUG") == "true" else None}
        )


@router.post("/voice/upload")
async def chat_voice_upload(
    audio_file: UploadFile = File(...),
    conversationId: Optional[str] = Form(None),
    saveToMemory: bool = Form(True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process voice chat: upload audio -> transcribe -> AI response
    
    Features:
    - Accept audio file upload
    - Transcribe using Whisper or similar
    - Process as text chat
    - Clean up temporary files
    """
    try:
        user_id = current_user.get("userId") or current_user.get("id")
        if not user_id:
            return send_error(
                status_code=400,
                message="Invalid user data"
            )
        
        # Verify subscription
        subscription = await auth_service.verify_user_subscription(user_id, "voice_chat")
        if not subscription:
            return send_error(
                status_code=403,
                message="Subscription required for voice chat",
                data={"feature": "voice_chat", "required": True}
            )
        
        # Validate audio file
        if not audio_file.content_type.startswith("audio/"):
            return send_error(
                status_code=400,
                message="Invalid file type. Audio files only.",
                data={"received": audio_file.content_type}
            )
        
        # Check file size (10MB limit)
        if audio_file.size > 10 * 1024 * 1024:
            return send_error(
                status_code=400,
                message="File too large. Maximum 10MB allowed.",
                data={"size": audio_file.size, "limit": 10485760}
            )
        
        temp_file_path = None
        try:
            # Save uploaded file temporarily
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file_path = temp_file.name
            
            contents = await audio_file.read()
            temp_file.write(contents)
            temp_file.close()
            
            # Transcribe audio
            transcription = await ai_service.transcribe_audio(temp_file_path)
            
            if not transcription or not transcription.strip():
                return send_error(
                    status_code=400,
                    message="Could not transcribe audio. Please try again.",
                )
            
            # Process as text chat
            chat_request = ChatTextRequest(
                message=transcription,
                conversationId=conversationId,
                saveToMemory=saveToMemory,
                metadata={"sourceType": "voice_upload", "originalFilename": audio_file.filename}
            )
            
            # Reuse text chat logic
            from app.routes.ai_chat import chat_text
            response = await chat_text(chat_request, current_user)
            
            # Add transcription to response
            if hasattr(response, 'body'):
                response_data = response.body.decode() if isinstance(response.body, bytes) else response.body
                if isinstance(response_data, dict) and response_data.get('data'):
                    response_data['data']['transcription'] = transcription
            
            return response
            
        finally:
            # Clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"Voice chat error: {e}")
        return send_error(
            status_code=500,
            message="Failed to process voice chat",
            data={"error": str(e) if os.getenv("DEBUG") == "true" else None}
        )


@router.get("/conversations")
async def get_user_conversations(
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's chat conversations"""
    try:
        user_id = current_user.get("userId") or current_user.get("id")
        
        # Get recent chat logs grouped by conversation
        chat_logs = await AiChatLog.find(
            AiChatLog.userId == user_id
        ).sort([("createdAt", -1)]).limit(limit).to_list()
        
        # Group by conversation ID
        conversations = {}
        for log in chat_logs:
            conv_id = log.conversationId
            if conv_id not in conversations:
                conversations[conv_id] = {
                    "conversationId": conv_id,
                    "lastMessage": log.userMessage,
                    "lastResponse": log.aiResponse,
                    "lastActivity": log.createdAt,
                    "messageCount": 0,
                    "totalTokens": 0
                }
            
            conversations[conv_id]["messageCount"] += 1
            conversations[conv_id]["totalTokens"] += sum(log.tokenUsage.values())
        
        # Convert to list and sort by last activity
        conversation_list = list(conversations.values())
        conversation_list.sort(key=lambda x: x["lastActivity"], reverse=True)
        
        return send_response(
            status_code=200,
            message="Conversations retrieved successfully",
            data={"conversations": conversation_list}
        )
        
    except Exception as e:
        print(f"Get conversations error: {e}")
        return send_error(
            status_code=500,
            message="Failed to retrieve conversations"
        )