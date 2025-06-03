import asyncio
from dotenv import load_dotenv
from livekit.agents import cli, AgentSession, Agent, JobContext, WorkerOptions
from livekit.plugins import openai, silero

load_dotenv()

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession(
        vad=silero.VAD.load(),  # Detect when user is speaking
        llm=openai.LLM(),       # Uses local Ollama (via OPENAI_API_BASE)
        stt=None,               # We'll add Whisper or whisper.cpp later
        tts=None                # We'll add Coqui TTS later
    )

    agent = Agent(instructions="You are a helpful AI voice assistant. Answer clearly and concisely.")

    await session.start(room=ctx.room, agent=agent)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))