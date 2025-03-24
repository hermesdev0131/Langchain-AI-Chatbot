import io
import asyncio
import logging
from fastapi import UploadFile
import azure.cognitiveservices.speech as speechsdk
from app.config import settings

logger = logging.getLogger(__name__)

async def transcribe(self, file: "UploadFile") -> str:
    # Read the uploaded WAV file.
    try:
        wav_bytes = await file.read()
        logger.info(f"Received WAV file of size {len(wav_bytes)} bytes")
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise e

    # Create an in-memory push audio stream and write the WAV bytes.
    try:
        push_stream = speechsdk.audio.PushAudioInputStream()
        push_stream.write(wav_bytes)
        push_stream.close()  # Signal end-of-stream.
        logger.info("Created in-memory push audio stream for transcription")
    except Exception as e:
        logger.error(f"Error creating push audio stream: {e}")
        raise e

    # Configure Azure Speech SDK with custom endpoint and key.
    speech_config = speechsdk.SpeechConfig(
        subscription=settings.AZURE_SPEECH_API_KEY,
        endpoint=settings.AZURE_SPEECH_ENDPOINT
    )
    # Set the recognition language to English.
    speech_config.speech_recognition_language = "en-US"

    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    logger.info("Sending audio stream for Azure transcription")
    try:
        # Offload the blocking call to a separate thread.
        result_future = speech_recognizer.recognize_once_async()
        result = await asyncio.to_thread(result_future.get)
        logger.info("Transcription response received")
    except Exception as e:
        logger.error(f"Error during Azure transcription: {e}")
        raise e

    # Retrieve error details if available.
    error_info = getattr(result, "errorDetails", "")
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        transcript_text = result.text
        logger.info(f"Transcription text (first 50 chars): {transcript_text[:50]}...")
        return transcript_text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        logger.error("No speech could be recognized. " + error_info)
        return ""
    else:
        logger.error(f"Speech recognition failed with reason: {result.reason}. " + error_info)
        return ""
