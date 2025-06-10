# tts_custom.py
import asyncio
import logging
from livekit.agents.tts import TTS, TTSCapabilities
from livekit.rtc import EventEmitter

logger = logging.getLogger(__name__)

# This class now implements both the async iterator and async context manager protocols.
class DuckTypedTTSStream:
    def __init__(self):
        self._text_queue = asyncio.Queue()
        self._event_queue = asyncio.Queue()
        self._main_task = asyncio.create_task(self._main_task())

    def push_text(self, text: str) -> None:
        logger.info(f"DuckTypedTTSStream: Received text chunk via push_text: '{text}'")

    async def aclose(self) -> None:
        logger.info("DuckTypedTTSStream aclose() called. Signaling end.")
        self._text_queue.put_nowait(None)  # Sentinel to end the main task
        await self._main_task

    async def _main_task(self):
        while True:
            text = await self._text_queue.get()
            if text is None:
                break
            # A real TTS would synthesize audio here.
        logger.info("DuckTypedTTSStream: Emitting 'finished' event to iterator.")
        await self._event_queue.put({"type": "finished"})
        await self._event_queue.put(None)  # Sentinel to stop the async iterator

    # --- Methods for Async Iterator Protocol ---
    def __aiter__(self):
        return self

    async def __anext__(self):
        event = await self._event_queue.get()
        if event is None:
            raise StopAsyncIteration
        return event

    # --- Methods for Async Context Manager Protocol ---
    async def __aenter__(self):
        logger.info("DuckTypedTTSStream __aenter__ called.")
        return self # The 'async with' statement will use this object

    async def __aexit__(self, exc_type, exc, tb):
        logger.info("DuckTypedTTSStream __aexit__ called, closing stream.")
        await self.aclose() # Ensure the stream is closed when the 'with' block exits


class DummyTTS(TTS):
    def __init__(self, sample_rate: int = 24000, num_channels: int = 1):
        super().__init__(
            capabilities=TTSCapabilities(streaming=True),
            sample_rate=sample_rate,
            num_channels=num_channels
        )
        logger.info(f"DummyTTS Initialized. Output format: {sample_rate}Hz, {num_channels}ch. Streaming: True")

    def stream(self) -> DuckTypedTTSStream:
        logger.info("DummyTTS.stream() called, returning a new DuckTypedTTSStream instance.")
        return DuckTypedTTSStream()

    async def synthesize(self, text: str, **kwargs) -> EventEmitter:
        logger.info(f"DummyTTS.synthesize() called for text: '{text}'.")
        event_emitter = EventEmitter()
        async def _task():
            await asyncio.sleep(0.01)
            event_emitter.emit("finished", {"type": "finished"})
        asyncio.create_task(_task())
        return event_emitter

    async def close(self):
        logger.info("DummyTTS close called.")
        pass