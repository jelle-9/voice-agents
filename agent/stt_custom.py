import asyncio
from faster_whisper import WhisperModel
import logging
import numpy as np
import resampy
from dataclasses import dataclass, field
from typing import List, Optional

from livekit.agents.stt import STTCapabilities
from livekit.rtc import EventEmitter, AudioFrame

logger = logging.getLogger("stt_custom")

# Define simple data classes that mimic what StreamAdapter/AgentSession expect.
# These have the necessary attributes to avoid the AttributeError.
@dataclass
class CustomSegment:
    text: str
    start: int # ms
    end: int   # ms

@dataclass
class CustomSTTAlternative:
    text: str
    language: Optional[str] = None
    confidence: float = 1.0
    segments: List[CustomSegment] = field(default_factory=list)

@dataclass
class CustomSTTEvent:
    type: str # "final_result" for non-streaming
    alternatives: List[CustomSTTAlternative] = field(default_factory=list)


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

    async def recognize(self, *, buffer: AudioFrame, **kwargs) -> CustomSTTEvent:
        # We will ALWAYS use the language configured during initialization (self._language)
        # This solves the "'NOT_GIVEN' is not a valid language code" error.
        current_transcribe_language = self._language
        
        logger.info(f"STT Recognize called with AudioFrame. Using language: {current_transcribe_language}")
        
        try:
            # Resampling logic
            audio_int16 = np.frombuffer(buffer.data, dtype=np.int16)
            if buffer.num_channels > 1:
                audio_int16 = audio_int16[::buffer.num_channels]
            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            if buffer.sample_rate != 16000:
                logger.info(f"Resampling audio from {buffer.sample_rate}Hz to 16000Hz.")
                audio_resampled = resampy.resample(audio_float32, sr_orig=buffer.sample_rate, sr_new=16000)
            else:
                audio_resampled = audio_float32

            # Transcription logic
            loop = asyncio.get_event_loop()
            segments_generator, info = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(audio_resampled, language=current_transcribe_language, beam_size=5)
            )

            final_text_parts = []
            custom_segments = []
            for segment in segments_generator:
                final_text_parts.append(segment.text)
                custom_segments.append(
                    CustomSegment(text=segment.text, start=int(segment.start * 1000), end=int(segment.end * 1000))
                )

            final_text = "".join(final_text_parts).strip()
            logger.info(f"STT Transcription result: '{final_text}'")

            alternative = CustomSTTAlternative(text=final_text, language=current_transcribe_language, segments=custom_segments)
            return CustomSTTEvent(type="final_result", alternatives=[alternative])

        except Exception as e:
            logger.error(f"STT Error during recognition: {e}")
            return CustomSTTEvent(type="final_result", alternatives=[])

    async def close(self):
        logger.info("CustomSTT close called.")
        pass