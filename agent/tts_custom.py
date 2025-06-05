import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Any, AsyncGenerator

from livekit.agents.tts import TTS, TTSCapabilities
try:
    from livekit.agents.tts import SynthesizedAudio
except ImportError:
    logger_tts_custom_fallback = logging.getLogger(__name__)
    logger_tts_custom_fallback.warning("livekit.agents.tts.SynthesizedAudio not found, defining CustomSynthesizedAudio.")
    @dataclass
    class CustomSynthesizedAudio: # type: ignore
        text: Optional[str] = None
        frames: List['AudioFrame'] = field(default_factory=list)
    SynthesizedAudio = CustomSynthesizedAudio # Use our custom one as an alias

from livekit.rtc import EventEmitter, AudioFrame

logger = logging.getLogger(__name__)

@dataclass
class CustomSynthesisEvent: # Our local definition
    type: str
    data: Optional[SynthesizedAudio] = None
    error: Optional[str] = None

class DummyTTS(TTS):
    def __init__(self, sample_rate: int = 24000, num_channels: int = 1):
        super().__init__(
            capabilities=TTSCapabilities(streaming=True),
            sample_rate=sample_rate,
            num_channels=num_channels
        )
        logger.info(f"DummyTTS Initialized. Output format: {sample_rate}Hz, {num_channels}ch. Streaming: True")

    # Corrected return type hint to use CustomSynthesisEvent
    async def stream(self, text_iterator: AsyncGenerator[str, None], **kwargs) -> AsyncGenerator[CustomSynthesisEvent, None]:
        logger.info("DummyTTS.stream() called.")
        async for text_chunk in text_iterator:
            logger.info(f"DummyTTS.stream(): Received text chunk: '{text_chunk}'. Doing nothing with audio.")
            pass

        logger.info("DummyTTS.stream(): Text iterator finished. Yielding 'finished' event.")
        yield CustomSynthesisEvent(type="finished", data=None)

    # Corrected return type hint's generic parameter to use CustomSynthesisEvent
    async def synthesize(self, text: str, **kwargs) -> EventEmitter[CustomSynthesisEvent]:
        if 'conn_options' in kwargs:
            logger.info(f"DummyTTS.synthesize called with conn_options: {kwargs['conn_options']}")
        
        logger.info(f"DummyTTS.synthesize: Received text to synthesize: '{text}'.")
        
        event_emitter = EventEmitter() # This will emit CustomSynthesisEvent

        async def _task():
            await asyncio.sleep(0.01)
            logger.info("DummyTTS.synthesize: Emitting 'finished' event.")
            event_emitter.emit("finished", CustomSynthesisEvent(type="finished", data=None))

        asyncio.create_task(_task())
        return event_emitter

    async def close(self):
        logger.info("DummyTTS close called.")
        pass