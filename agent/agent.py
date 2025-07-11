import asyncio
from dotenv import load_dotenv
import logging
import os

from livekit.agents import cli, AgentSession, Agent, JobContext, WorkerOptions
# Correct way to import the LLM plugin class
from livekit.plugins.openai import LLM as OpenAI_LLM # Alias to avoid conflict with openai module
from livekit.plugins import silero
from openai import AsyncOpenAI # Import the AsyncOpenAI client

from stt_custom import CustomSTT
from tts_custom import DummyTTS

load_dotenv()

# --- NEW LOGGING SETUP ---
# Configure a more readable format
LOG_FORMAT = '%(asctime)s %(levelname)-8s [%(name)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Set up logging for our own scripts and silence noisy libraries
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
logging.getLogger("livekit.agents").setLevel(logging.WARNING)
logging.getLogger("livekit.rtc").setLevel(logging.WARNING)
logging.getLogger("livekit").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("faster_whisper").setLevel(logging.WARNING)
logging.getLogger("numba").setLevel(logging.WARNING) # <-- Add this line to silence numba

# Get our specific logger
logger = logging.getLogger("agent_script")
# --- END NEW LOGGING SETUP ---

async def entrypoint(ctx: JobContext):
    agent_identity = os.getenv("LIVEKIT_IDENTITY", "default-agent-identity")
    logger.info(f"Agent job received. Room: {ctx.room.name}, Configured Identity: {agent_identity}")

    await ctx.connect()
    logger.info(f"Agent connected to LiveKit server. Room: {ctx.room.name}, Actual Agent Identity: {ctx.agent.identity if ctx.agent else agent_identity}")

    stt_service = CustomSTT(model_size="base", device="cpu", compute_type="int8", language="de")
    logger.info("STT service initialized.")

    # Explicitly create an OpenAI client configured for Ollama
    ollama_client = AsyncOpenAI(
        base_url=os.getenv("OPENAI_API_BASE"), # Should be http://localhost:11434/v1
        api_key=os.getenv("OPENAI_API_KEY")    # Should be "ollama"
    )
    logger.info(f"OpenAI client configured for Ollama. Base URL: {os.getenv('OPENAI_API_BASE')}, API Key: {os.getenv('OPENAI_API_KEY')}")

    tts_service = DummyTTS()
    logger.info("Dummy TTS service initialized.")

    session = AgentSession(
        vad=silero.VAD.load(),
        llm=OpenAI_LLM(
            model="mistral", # Specify the Ollama model name
            client=ollama_client # Pass the pre-configured client
        ),
        stt=stt_service,
        tts=tts_service
    )
    logger.info("AgentSession created with VAD, LLM, STT.")

    # ... (rest of your agent.py code: agent_instance, event handlers, session.start) ...
    agent_instance = Agent(
        instructions="You are a helpful AI voice assistant for German. Answer clearly and concisely in German."
    )
    logger.info("Agent instance created.")

    @session.on("track_subscribed")
    def on_track_subscribed_sync(track, publication, participant):
        logger.info(f"Participant {participant.identity} subscribed to track {track.sid} ({track.kind})")
        if track.kind == "audio":
            logger.info(f"Audio track subscribed from {participant.identity}. AgentSession will now process this audio.")

    @session.on("stt_update")
    def on_stt_update_sync(text: str, final: bool):
        logger.info(f"STT Update: '{text}', Final: {final}")
        if final:
            logger.info(f"Final STT Result: '{text}' - This will be sent to LLM.")

    @session.on("llm_response")
    def on_llm_response_sync(text: str, final: bool):
        logger.info(f"LLM Response: '{text}', Final: {final}")
        if final:
            logger.info(f"Final LLM Response: '{text}' - This would be sent to TTS if implemented.")

    logger.info(f"Starting agent session in room '{ctx.room.name}'...")
    try:
        await session.start(room=ctx.room, agent=agent_instance)
        logger.info(f"Agent session started successfully in room '{ctx.room.name}'. Listening for participants...")
    except Exception as e:
        logger.error(f"Error during agent session start: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting LiveKit Agent CLI...")
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))