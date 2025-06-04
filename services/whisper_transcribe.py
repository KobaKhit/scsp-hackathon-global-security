import os
from openai import AsyncOpenAI
from typing import Dict, Any
from .config import Config

class WhisperService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=Config.get_openai_api_key()
        )
    
    async def transcribe_audio(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """Transcribe audio using Whisper API"""
        try:
            with open(audio_path, "rb") as audio_file:
                # Basic transcription
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="json",
                    temperature=0.0
                )
            
            # Enhanced analysis with GPT-4o
            analysis = await self._analyze_transcript(transcript.text)
            
            return {
                "transcription": transcript.text,
                "language": transcript.language if hasattr(transcript, 'language') else 'unknown',
                "analysis": analysis,
                "duration": getattr(transcript, 'duration', None)
            }
            
        except Exception as e:
            return {
                "transcription": f"Error transcribing audio: {str(e)}",
                "language": "unknown",
                "analysis": "Unable to analyze due to transcription error",
                "duration": None
            }
    
    async def _analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyze transcript for intelligence insights"""
        try:
            analysis_prompt = f"""Analyze this diplomatic/intelligence transcript for:

1. Key topics and themes
2. Important decisions or agreements
3. Tensions or concerns raised
4. Security implications
5. Action items or next steps
6. Sentiment and tone
7. Key participants (if identifiable)

Transcript:
{transcript}

Provide a structured intelligence analysis focusing on security and diplomatic implications."""

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an intelligence analyst specializing in diplomatic and security communications."
                    },
                    {
                        "role": "user", 
                        "content": analysis_prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return {
                "intelligence_summary": response.choices[0].message.content,
                "confidence": "high"
            }
            
        except Exception as e:
            return {
                "intelligence_summary": f"Error analyzing transcript: {str(e)}",
                "confidence": "error"
            }

# Global instance
whisper_service = WhisperService()

async def transcribe_audio(audio_path: str, language: str = None) -> Dict[str, Any]:
    """Transcribe and analyze audio files"""
    return await whisper_service.transcribe_audio(audio_path, language) 