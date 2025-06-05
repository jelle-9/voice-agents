import asyncio
from faster_whisper import WhisperModel
import logging # For better debugging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomSTT:
    def __init__(self, model_size="base", device="cuda", compute_type="float16", language="de"):
        logger.info(f"Initializing CustomSTT with model: {model_size}, device: {device}, lang: {language}")
        try:
            # For CPU, you might prefer "cpu" and "int8" or "float32"
            # For your GTX 1060, "cuda" and "float16" should be okay for smaller models.
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            self.language = language
            logger.info("CustomSTT model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            logger.error("Ensure you have the correct model files and dependencies (like CUDA for GPU).")
            logger.error("You might need to download the model first if it's not cached by faster-whisper.")
            # To download models, faster-whisper does it automatically when WhisperModel is initialized.
            # If it fails, it could be a path issue or internet connectivity for the first download.
            raise

    async def transcribe(self, audio_path: str) -> str:
        logger.info(f"Transcribing audio file: {audio_path}")
        try:
            # faster-whisper's transcribe method is synchronous,
            # so we run it in a thread pool executor to avoid blocking asyncio event loop.
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None, # Uses default ThreadPoolExecutor
                lambda: self.model.transcribe(audio_path, language=self.language, beam_size=5)
            )

            detected_lang = info.language
            lang_probability = info.language_probability
            logger.info(f"Detected language: {detected_lang} with probability {lang_probability:.2f}")

            transcription = " ".join([segment.text for segment in segments])
            logger.info(f"Transcription: {transcription}")
            return transcription.strip()
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""