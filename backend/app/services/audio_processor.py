"""Audio transcription service using HuggingFace Whisper."""


import logging
from pathlib import Path

from transformers import pipeline
from langchain_core.documents import Document

import os
os.environ["PATH"] += r";C:\ffmpeg\bin"

logger=logging.getLogger(__name__)

SUPPORTED_AUDIO_EXTENSIONS={".mp3", ".wav", ".m4a", ".webm", ".ogg", ".flac"}

class AudioProcessor:
    """
    Handle audio file transcription using HuggingFace Whisper model
    """
    def __init__(self):
        logger.info("Loading Whisper model...")
        self.pipe=pipeline(
            task="automatic-speech-recognition",
            model="openai/whisper-base",
            chunk_length_s=30, #30 secs
            stride_length_s=5, #overlap 5 secs
        )
        logger.info("Whisper model loaded successfully!")

    @staticmethod
    def is_audio_file(filename:str)->bool:
        """Check if a file is a supported audio format"""
        return Path(filename).suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS

    async def transcribe(self, file_path:Path)->Document:
        """
        Transcribe an audio file using Whisper model.

        Args:
            file_path: Path to the audio file.

        Returns:
            A Document containing the transcribed text with metadata. 
        """
        suffix=file_path.suffix.lower()
        if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
            raise ValueError(
                f"Unsupported audio format {suffix}."
                f"Supported: {', '.join(SUPPORTED_AUDIO_EXTENSIONS)}"
            )
        logger.info(f"Transribing audio file: {file_path.name}")

        try:
            #Whisper pipeline run sync -> run in threadpool to not block FastAPI
            import asyncio
            loop=asyncio.get_event_loop()
            result=await loop.run_in_executor(
                None,   #using default threadpool
                self._transcribe_sync,
                str(file_path),
            )

            text=result["text"].strip()
            logger.info(f"Transcription completed: {len(text)} characters")

            return Document(
                page_content=text,
                metadata={
                    "source":file_path.name,
                    "file_type": suffix.lstrip("."),
                    "content_type":"audio_transcription",
                    "model":"openai/whisper-base",
                },
            )
        
        except Exception as e:
            logger.error(f"Failed to transcribe {file_path.name}: {e}")
            raise

    def _transcribe_sync(self, file_path_str:str)->dict:
        """
        Sync wrapper for Whisper pipeline.
        Run in threadpool to not blocking async in event loop
        """
        result= self.pipe(
            file_path_str,
            generate_kwargs={"language":"vietnamese"},
            return_timestamps=False,

        )
        # DEBUG: print text
        print(f"\n{'='*60}")
        print(f"WHISPER TRANSCRIPTION RESULT:")
        print(f"'-"*60)
        print(result["text"])
        print(f"\n{'='*60}")
        return result
