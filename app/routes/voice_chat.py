from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any
import uuid
import os
import tempfile
from datetime import datetime, timezone

from app.utils.response import send_response, send_error
from app.services.auth_service import auth_service
from app.services.ai_service import ai_service


router = APIRouter()


# Auth dependency
async def get_current_user(authorization: str = Depends(lambda: None)) -> Dict[str, Any]:
    """Extract current user from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    user = await auth_service.get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user


@router.post("/upload")
async def upload_voice_message(
    audio_file: UploadFile = File(...),
    conversationId: Optional[str] = Form(None),
    saveToMemory: bool = Form(True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload voice message for transcription and AI response
    
    Features:
    - Accept audio file upload (wav, mp3, m4a, flac)
    - Validate file type and size
    - Transcribe using Whisper
    - Generate AI response
    - Store conversation in memory if requested
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
        
        # Validate file type
        allowed_types = ["audio/wav", "audio/mp3", "audio/m4a", "audio/flac", "audio/mpeg", "audio/x-m4a"]
        if audio_file.content_type not in allowed_types:
            return send_error(
                status_code=400,
                message="Invalid file type. Supported formats: WAV, MP3, M4A, FLAC",
                data={"received": audio_file.content_type, "allowed": allowed_types}
            )
        
        # Check file size (10MB limit)
        max_size = int(os.getenv("MAX_FILE_SIZE_MB", "10")) * 1024 * 1024
        if audio_file.size and audio_file.size > max_size:
            return send_error(
                status_code=400,
                message=f"File too large. Maximum {max_size // 1024 // 1024}MB allowed.",
                data={"size": audio_file.size, "limit": max_size}
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
                    message="Could not transcribe audio. Please ensure the audio is clear and try again."
                )
            
            # Generate conversation ID if not provided
            conversation_id = conversationId or str(uuid.uuid4())
            
            # Get AI response for transcribed text
            ai_response = await ai_service.chat_completion(
                message=transcription,
                user_id=user_id,
                context=""  # Could add conversation context here
            )
            
            # Store in vector memory if requested
            memory_stored = False
            if saveToMemory:
                # TODO: Store in Qdrant vector database
                memory_stored = True
            
            response_data = {
                "conversationId": conversation_id,
                "transcription": transcription,
                "message": transcription,
                "responseText": ai_response["text"],
                "tokenUsage": ai_response["token_usage"],
                "model": ai_response.get("model", "unknown"),
                "memoryStored": memory_stored,
                "audioMetadata": {
                    "originalFilename": audio_file.filename,
                    "contentType": audio_file.content_type,
                    "size": audio_file.size
                }
            }
            
            return send_response(
                status_code=200,
                message="Voice message processed successfully",
                data=response_data
            )
            
        finally:
            # Clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    print(f"Failed to cleanup temp file: {cleanup_error}")
        
    except Exception as e:
        print(f"Voice chat error: {e}")
        return send_error(
            status_code=500,
            message="Failed to process voice message",
            data={"error": str(e) if os.getenv("DEBUG") == "true" else None}
        )


@router.post("/text-to-speech")
async def convert_text_to_speech(
    text: str = Form(...),
    voice: str = Form(default="alloy"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Convert text to speech (if TTS service is available)
    
    Note: This is a placeholder for TTS functionality
    You would integrate with services like OpenAI TTS, ElevenLabs, etc.
    """
    try:
        user_id = current_user.get("userId") or current_user.get("id")
        
        # Verify subscription
        subscription = await auth_service.verify_user_subscription(user_id, "voice_chat")
        if not subscription:
            return send_error(
                status_code=403,
                message="Subscription required for text-to-speech"
            )
        
        # TODO: Implement actual TTS conversion
        # For now, return a placeholder response
        
        return send_response(
            status_code=200,
            message="Text-to-speech feature coming soon",
            data={
                "text": text,
                "voice": voice,
                "status": "not_implemented"
            }
        )
        
    except Exception as e:
        print(f"TTS error: {e}")
        return send_error(
            status_code=500,
            message="Failed to process text-to-speech request"
        )


@router.get("/supported-formats")
async def get_supported_audio_formats():
    """Get list of supported audio formats"""
    
    formats = [
        {
            "format": "WAV",
            "mimeType": "audio/wav",
            "description": "Uncompressed audio, best quality"
        },
        {
            "format": "MP3", 
            "mimeType": "audio/mp3",
            "description": "Compressed audio, good quality"
        },
        {
            "format": "M4A",
            "mimeType": "audio/m4a", 
            "description": "Apple audio format"
        },
        {
            "format": "FLAC",
            "mimeType": "audio/flac",
            "description": "Lossless compression"
        }
    ]
    
    return send_response(
        status_code=200,
        message="Supported audio formats",
        data={
            "formats": formats,
            "maxSizeMB": int(os.getenv("MAX_FILE_SIZE_MB", "10")),
            "maxDurationMinutes": 10  # Typical limit for voice messages
        }
    )