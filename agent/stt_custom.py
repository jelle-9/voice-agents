import asyncio
from faster_whisper import WhisperModel
import logging
import numpy as np
from dataclasses import dataclass, field # For creating simple data classes
from typing import List, Optional # For type hinting

from livekit.agents.stt import STTCapabilities # This import is valid
from livekit.rtc import EventEmitter, AudioFrame

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define simple data classes that mimic what StreamAdapter expects for a final result
@dataclass
class CustomSegmentData:
    text: str
    start_time: int # ms
    end_time: int   # ms
    language: Optional[str] = None
    # final: bool = True # Segments are part of a final result

@dataclass
class CustomSTTAlternative:
    text: str
    language: Optional[str] = None
    confidence: float = 1.0 # Default to 1.0 for faster-whisper final result
    segments: List[CustomSegmentData] = field(default_factory=list)
    # final: bool = True # This alternative is part of a final event

@dataclass
class CustomSTTEvent:
    type: str # "final_result", "interim_result", "error"
    alternatives: List[CustomSTTAlternative] = field(default_factory=list)
    # final: bool attribute might be directly on STTEvent for some SDK versions,
    # or implied by the type/alternatives. For now, let's rely on type="final_result".
    # The STTData object in official plugins has a 'final' attribute.
    # Let's try without a top-level 'final' on CustomSTTEvent first.
    # If StreamAdapter checks for event.final, we might need to add it.

class CustomSTT(EventEmitter):
    def __init__(self, model_size="base", device="cpu", compute_type="int8", language="de"):
        super().__init__()
        logger.info(f"Initializing CustomSTT with model: {model_size}, device: {device}, compute_type: {compute_type}, lang: {language}")
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            self._language = language
            self.capabilities = STTCapabilities(streaming=False, interim_results=False)
            logger.info("CustomSTT model loaded successfully. Capabilities set.")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise

    async def recognize(self, *, buffer: AudioFrame, **kwargs) -> CustomSTTEvent: # Return our custom event type
        language_arg = kwargs.get('language')
        current_transcribe_language = self._language

        if language_arg is not None and language_arg != self._language:
            logger.warning(f"Recognize called with language '{language_arg}' from StreamAdapter, "
                           f"but CustomSTT instance is configured for '{self._language}'. "
                           f"Using configured language: '{self._language}'.")
        
        logger.info(f"STT Recognize called with AudioFrame. Buffer length: {len(buffer.data)}, "
                    f"Sample rate: {buffer.sample_rate}, Channels: {buffer.num_channels}. "
                    f"Language for transcription: {current_transcribe_language}")
        try:
            if buffer.sample_rate != 16000:
                logger.warning(f"Input sample rate {buffer.sample_rate}Hz is not 16kHz. Transcription quality may be affected.")

            audio_int16 = np.frombuffer(buffer.data, dtype=np.int16)
            if buffer.num_channels > 1:
                audio_int16 = audio_int16[::buffer.num_channels]

            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            loop = asyncio.get_event_loop()
            segments_generator, info = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(audio_float32, language=current_transcribe_language, beam_size=5)
            )

            model_detected_language = info.language
            lang_probability = info.language_probability
            logger.info(f"STT Detected language by model: {model_detected_language} with probability {lang_probability:.2f}")

            custom_stt_segments = []
            full_text_parts = []
            for segment in segments_generator:
                full_text_parts.append(segment.text)
                custom_stt_segments.append(
                    CustomSegmentData(
                        text=segment.text,
                        start_time=int(segment.start * 1000), # ms
                        end_time=int(segment.end * 1000),     # ms
                        language=model_detected_language
                    )
                )
            
            final_text = "".join(full_text_parts).strip()
            logger.info(f"STT Transcription result: '{final_text}'")

            # Construct our custom STTEvent-like object
            alternative = CustomSTTAlternative(
                text=final_text,
                language=current_transcribe_language, # Language requested for transcription
                segments=custom_stt_segments
            )
            return CustomSTTEvent(type="final_result", alternatives=[alternative])

        except Exception as e:
            logger.error(f"STT Error during recognition: {e}")
            error_alternative = CustomSTTAlternative(text=str(e), language=current_transcribe_language)
            return CustomSTTEvent(type="error", alternatives=[error_alternative])

    async def close(self):
        logger.info("CustomSTT close called.")
        pass