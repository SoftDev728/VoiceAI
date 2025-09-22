import utils.transport
import utils.session
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

# Import our services and managers
from services.conversation_manager import conversation_manager
from services.audio_service import audio_service
from storage.memory_storage import memory_storage
from storage.sheets_manager import sheets_manager
from config import Config

# Initialize FastAPI app
app = FastAPI(
    title="Hospital Appointment Booking System",
    description="AI-powered appointment booking system for Surat Hospital",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class TextChatRequest(BaseModel):
    text: str
    user_id: Optional[str] = "default_user"

class ResetConversationRequest(BaseModel):
    user_id: Optional[str] = "default_user"

class ChatResponse(BaseModel):
    response: str
    user_id: str
    status: str

class StatusResponse(BaseModel):
    message: str
    status: str

# Utility function for session management
def get_or_create_user_id(request: Request) -> str:
    """Generate or retrieve user ID for session management"""
    # Check for session ID in headers
    session_id = request.headers.get('x-session-id')
    if session_id:
        return session_id
    
    # Generate new session ID
    return str(uuid.uuid4())

@app.post("/voice-chat")
async def voice_chat(request: Request, audio_file: UploadFile = File(...)):
    """
    Voice chat endpoint - accepts audio input and returns audio response
    """
    try:
        print(f"🎤 Received audio file: {audio_file.filename}, content_type: {audio_file.content_type}")
        
        # Read audio content
        audio_content = await audio_file.read()
        
        # Convert speech to text
        text = await audio_service.process_audio_file(
            audio_content, 
            audio_file.filename or "audio.webm"
        )
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        print(f"👤 User said: {text}")
        
        # Generate user ID for this session
        user_id = get_or_create_user_id(request)
        
        # Process the message using our conversation manager
        assistant_response = conversation_manager.process_user_message(text, user_id)
        
        if not assistant_response:
            assistant_response = f"I heard you say '{text}'. How can I help you with your appointment?"
        
        print(f"🤖 Assistant response: {assistant_response}")
        
        # Convert response to audio stream
        async def generate_audio():
            async for chunk in audio_service.text_to_speech(assistant_response):
                yield chunk
        
        return StreamingResponse(
            generate_audio(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=response.mp3",
                "X-Session-ID": user_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in voice chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text-chat", response_model=ChatResponse)
async def text_chat(request: TextChatRequest):
    """
    Text-based chat endpoint for testing and web interface
    """
    try:
        text = request.text.strip()
        user_id = request.user_id or "default_user"
        
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        print(f"💬 Text chat - User {user_id} said: {text}")
        
        # Process message with conversation memory
        response = conversation_manager.process_user_message(text, user_id)
        
        return ChatResponse(
            response=response,
            user_id=user_id,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Text chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset-conversation", response_model=StatusResponse)
async def reset_user_conversation(request: ResetConversationRequest):
    """
    Reset conversation for a specific user
    """
    try:
        user_id = request.user_id or "default_user"
        conversation_manager.reset_conversation(user_id)
        
        return StatusResponse(
            message=f"Conversation reset for user {user_id}",
            status="success"
        )
    except Exception as e:
        print(f"❌ Reset conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/appointments")
async def get_appointments():
    """
    Get all appointments from memory storage
    """
    try:
        response = memory_storage.get_all_appointments()
        return response.to_json()
    except Exception as e:
        print(f"❌ Error getting appointments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/appointments/sheets")
async def get_appointments_from_sheets():
    """
    Get all appointments from Google Sheets
    """
    try:
        response = sheets_manager.get_all_appointments()
        return response.to_json()
    except Exception as e:
        print(f"❌ Error getting appointments from sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_system_stats():
    """
    Get system statistics
    """
    try:
        conversation_stats = conversation_manager.get_conversation_stats()
        
        return {
            "hospital_info": {
                "name": Config.HOSPITAL_NAME,
                "address": Config.HOSPITAL_ADDRESS,
                "phone": Config.HOSPITAL_PHONE,
                "opd_hours": Config.OPD_HOURS
            },
            "system_status": {
                "google_sheets_connected": sheets_manager.is_connected(),
                "llm_model": Config.LLM_MODEL,
                "tts_model": Config.TTS_MODEL,
                "stt_model": Config.STT_MODEL
            },
            "conversation_stats": conversation_stats,
            "storage_info": {
                "sheets_url": Config.GOOGLE_SHEETS_URL if sheets_manager.is_connected() else "Not connected"
            }
        }
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup")
async def cleanup_old_sessions():
    """
    Cleanup old inactive sessions (24 hours)
    """
    try:
        cleaned_count = conversation_manager.cleanup_old_conversations(24)
        return StatusResponse(
            message=f"Cleaned up {cleaned_count} old sessions",
            status="success"
        )
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Hospital Appointment Booking System",
        "version": "2.0.0",
        "components": {
            "conversation_manager": "operational",
            "audio_service": "operational",
            "memory_storage": "operational",
            "google_sheets": "connected" if sheets_manager.is_connected() else "disconnected"
        }
    }

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": f"{Config.HOSPITAL_NAME} Appointment Booking System",
        "version": "2.0.0",
        "endpoints": {
            "voice_chat": "POST /voice-chat - Voice input for appointment booking",
            "text_chat": "POST /text-chat - Text input for appointment booking",
            "reset": "POST /reset-conversation - Reset user conversation",
            "appointments": "GET /appointments - Get all appointments",
            "appointments_sheets": "GET /appointments/sheets - Get appointments from Google Sheets",
            "stats": "GET /stats - System statistics",
            "cleanup": "POST /cleanup - Cleanup old sessions",
            "health": "GET /health - Health check"
        },
        "hospital_info": {
            "name": Config.HOSPITAL_NAME,
            "address": Config.HOSPITAL_ADDRESS,
            "phone": Config.HOSPITAL_PHONE,
            "opd_hours": Config.OPD_HOURS
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 Hospital Appointment Booking System v2.0 starting up...")
    print(f"🏥 {Config.HOSPITAL_NAME}")
    print(f"📍 {Config.HOSPITAL_ADDRESS}")
    print(f"📞 {Config.HOSPITAL_PHONE}")
    
    if sheets_manager.is_connected():
        print("✅ Google Sheets integration active")
    else:
        print("⚠️ Google Sheets integration disabled - using local storage only")
    
    print("✅ All systems ready!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("🔄 Shutting down Hospital Appointment Booking System...")
    # Cleanup any resources if needed
    print("✅ Shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)