import tempfile
import os
from typing import AsyncGenerator, BinaryIO
from openai import AsyncOpenAI
from config import Config

class AudioService:
    """Service for handling audio processing (STT and TTS)"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
    
    async def speech_to_text(self, audio_file: BinaryIO, filename: str = "audio.webm") -> str:
        """Convert speech to text using Whisper"""
        try:
            print(f"🎤 Processing audio file: {filename}")
            
            # Ensure the file pointer is at the beginning
            audio_file.seek(0)
            
            transcript_response = await self.client.audio.transcriptions.create(
                model=Config.STT_MODEL,
                file=audio_file
            )
            
            text = transcript_response.text
            print(f"📝 Transcribed text: {text}")
            return text
            
        except Exception as e:
            print(f"❌ Speech-to-text error: {e}")
            raise Exception(f"Speech recognition error: {e}")
    
    async def text_to_speech(self, text: str) -> AsyncGenerator[bytes, None]:
        """Convert text to speech using OpenAI TTS"""
        try:
            print(f"🔊 Converting text to speech: {text[:50]}...")
            
            async with self.client.audio.speech.with_streaming_response.create(
                model=Config.TTS_MODEL,
                voice=Config.TTS_VOICE,
                input=text,
                response_format='mp3'
            ) as response:
                async for chunk in response.iter_bytes():
                    yield chunk
                    
        except Exception as e:
            print(f"❌ Text-to-speech error: {e}")
            raise Exception(f"TTS error: {e}")
    
    async def process_audio_file(self, audio_content: bytes, filename: str = "audio.webm") -> str:
        """Process audio file content and return transcription"""
        tmp_file_path = None
        try:
            # Create temporary file for audio processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
                tmp_file.write(audio_content)
                tmp_file_path = tmp_file.name
            
            # Convert speech to text
            with open(tmp_file_path, 'rb') as audio_file_obj:
                return await self.speech_to_text(audio_file_obj, filename)
                
        finally:
            # Clean up temporary file
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except Exception as e:
                    print(f"⚠️ Error cleaning up temporary file: {e}")

# Global audio service instance
audio_service = AudioService()