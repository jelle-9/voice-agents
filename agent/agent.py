import asyncio
from dotenv import load_dotenv
import logging

from livekit.agents import cli, AgentSession, Agent, JobContext, WorkerOptions
from livekit.plugins import openai, silero # openai is for the Ollama connection

# Assuming stt_custom.py is in the same directory
from stt_custom import CustomSTT

load_dotenv()

# Configure basic logging for the agent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def entrypoint(ctx: JobContext):
    logger.info(f"Agent connecting to room: {ctx.room.name} with identity: {ctx.participant.identity}")
    await ctx.connect()
    logger.info("Agent connected successfully.")

    # Initialize STT. You can change model_size, device, etc.
    # For your GTX 1060, 'base' or 'small' on GPU ('cuda', 'float16') is a good start.
    # If GPU struggles, try 'cpu' and 'int8'.
    stt_service = CustomSTT(model_size="base", device="cuda", compute_type="float16", language="de")

    session = AgentSession(
        vad=silero.VAD.load(),
        llm=openai.LLM(), # Uses local Ollama via OPENAI_API_BASE from .env
        stt=stt_service,
        tts=None # We'll add local TTS later
    )

    logger.info("AgentSession created. Starting session...")
    agent = Agent(instructions="You are a helpful AI voice assistant for German. Answer clearly and concisely in German.")

    try:
        await session.start(room=ctx.room, agent=agent)
        # Keep the agent running until a disconnect or error
        # session.start is not a blocking call in the same way as run, so we might need to keep it alive.
        # The cli.run_app handles the lifecycle for us usually.
        logger.info("Agent session started. Listening for events...")
    except Exception as e:
        logger.error(f"Error during agent session start: {e}")

if __name__ == "__main__":
    # This sets up the CLI and worker options.
    # The .env file should define LIVEKIT_ROOM and LIVEKIT_IDENTITY for the 'dev' command.
    # e.g., LIVEKIT_ROOM=test
    #       LIVEKIT_IDENTITY=ai-german-agent
    logging.info("Starting LiveKit Agent CLI...")
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))