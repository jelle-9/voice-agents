# Local Open-Source Voice Agent with LiveKit

This project demonstrates a locally runnable voice agent pipeline using LiveKit for real-time communication, local Speech-to-Text (STT) with `faster-whisper`, a local Large Language Model (LLM) via Ollama, and a placeholder for Text-to-Speech (TTS). The primary goal is to understand how these components work together.

## Current Features

* **LiveKit Server**: Self-hosted for managing WebRTC sessions.
* **Local STT**: Custom `faster-whisper` integration for German speech-to-text (runs on CPU).
* **Local LLM**: Uses Ollama (e.g., with the `mistral` model) for text generation, accessed via an OpenAI-compatible API.
* **Python Agent**: `livekit-agents` based Python application that orchestrates VAD, STT, and LLM.
* **Web Frontend**: A Next.js example from `livekit/components-js` for interacting with the agent.
* **Text-based Interaction**: Currently, the agent processes voice to text, gets an LLM response as text (logged to console), and does not yet have audible speech output (TTS is a dummy).

## Prerequisites

Ensure you have the following software installed on your system (Linux, e.g., Ubuntu/Mint):

1.  **Docker & Docker Compose**: For running the LiveKit server.
    * [Install Docker](https://docs.docker.com/engine/install/)
    * [Install Docker Compose](https://docs.docker.com/compose/install/)
2.  **Python**: Version 3.12.x is used in this project.
    * `python3 --version`
    * `pip --version`
    * `python3-venv` package (e.g., `sudo apt install python3.12-venv`)
3.  **Node.js and pnpm**: For running the frontend example.
    * Node.js (e.g., v18+): `node --version`
    * npm (comes with Node.js): `npm --version`
    * pnpm: `sudo npm install -g pnpm`
4.  **Ollama**: For running local LLMs.
    * [Install Ollama](https://ollama.com/download)
5.  **Git**: For version control and cloning repositories.
6.  **Build Essentials & CMake** (for STT components if built from source, already done for `faster-whisper` via pip):
    * `sudo apt install build-essential cmake` (likely already done during previous steps)

## Directory Structure

voice-agents/
├── agent/                     # Python voice agent logic, venv, and custom STT/TTS
│   ├── agent.py
│   ├── stt_custom.py
│   ├── tts_custom.py          # (Contains DummyTTS for now)
│   ├── requirements.txt
│   └── .env                   # (Gitignored - holds API keys, URLs)
├── livekit-frontend-example/  # Cloned livekit/components-js for frontend
│   └── examples/
│       └── nextjs/            # The Next.js frontend example
│           └── .env.local     # (Gitignored - holds frontend env vars)
├── livekit-server/            # LiveKit server Docker configuration
│   ├── docker-compose.yaml
│   └── livekit.yaml
└── README.md                  # This file

## Setup and Running Instructions

**Important**: Before starting, navigate to the root directory where you cloned this `voice-agents` project. All `cd` commands below will assume you are starting from this project root, unless specified otherwise.

Each main component (Ollama, LiveKit Server, Python Agent, Frontend) typically runs in its **own separate terminal window**.

**1. Start Ollama LLM Server**

* Open a new terminal.
* Pull and run your desired model (e.g., `mistral`). If `mistral` is not yet pulled, this command will download it first.
    ```bash
    ollama run mistral
    ```
* Keep this terminal open. Ollama serves its API, usually at `http://localhost:11434`.

**2. Start LiveKit Server**

* Open a new terminal.
* Navigate to the LiveKit server configuration directory:
    ```bash
    cd ./livekit-server/
    ```
* The `livekit.yaml` file configures the server (default ports are generally fine for local use).
* Start the server using Docker Compose:
    ```bash
    docker compose up -d
    ```
* To check status: `docker compose ps`. To see logs: `docker compose logs livekit`.

**3. Set Up and Run the Python Voice Agent**

* Open a new terminal.
* Navigate to the agent directory:
    ```bash
    cd ./agent/
    ```
* **Create and activate Python virtual environment** (first time setup):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *(For subsequent runs, just activate it: `source venv/bin/activate`)*
* **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
* **Configure the agent**:
    Create a file named `.env` in the `agent/` directory with the following content:
    ```env
    LIVEKIT_URL=http://localhost:7880
    LIVEKIT_API_KEY=devkey
    LIVEKIT_API_SECRET=secret

    # For Ollama (ensure Ollama serves the OpenAI-compatible API at /v1)
    OPENAI_API_BASE=http://localhost:11434/v1
    OPENAI_API_KEY=ollama # Can be any non-empty string for Ollama

    LIVEKIT_ROOM=test-german-agent # Room the agent will join
    LIVEKIT_IDENTITY=ai-voice-agent  # Agent's identity in the room
    ```
* **Run the agent**:
    ```bash
    python agent.py dev
    ```
* Keep this terminal open. You should see logs indicating it started, connected to LiveKit, and loaded STT.

**4. Set Up and Run the Frontend Example**

* Open a new terminal.
* **Navigate to the root of the cloned `components-js` repository within this project**:
    ```bash
    cd ./livekit-frontend-example/
    ```
* **Install monorepo dependencies and build packages**:
    This step installs all dependencies for the `components-js` monorepo and builds its internal packages (like `@livekit/components-styles` and `@livekit/components-react`) so the example app can use them.
    ```bash
    pnpm install
    pnpm build # This runs 'turbo run build'
    ```
* **Navigate to the Next.js example directory**:
    ```bash
    cd examples/nextjs/
    ```
* **Configure the frontend environment**:
    Create a file named `.env.local` in this directory (`./livekit-frontend-example/examples/nextjs/.env.local`) with the following content:
    ```env
    # Tells the LiveKitRoom component which server to connect to
    NEXT_PUBLIC_LK_SERVER_URL=ws://<your-laptop-ip>:7880

    # Tells the useToken hook where the example's internal token-generating API route is
    NEXT_PUBLIC_LK_TOKEN_ENDPOINT=/api/livekit/token

    # These are used by the /api/livekit/token Next.js API route (server-side)
    # to generate tokens for your LiveKit server.
    LIVEKIT_API_KEY=devkey
    LIVEKIT_API_SECRET=secret
    ```
    * **Important**: Replace `<your-laptop-ip>` with the actual Local Area Network (LAN) IP address of the machine running the LiveKit server.
        * On Linux, you can usually find this by running `ip addr show` in the terminal and looking for the `inet` address under your active network interface (e.g., `eth0` or `wlan0`).
        * Do **not** use `localhost` or `127.0.0.1` for this variable if you intend to test the frontend from *other devices* on your network. If testing the browser on the *same machine*, `ws://localhost:7880` can be used.
* **Run the frontend development server**:
    Use the command that worked for you (likely `pnpm dev:next` which runs `turbo run dev --filter=@livekit/component-example-next...`, or try `pnpm run dev` directly in this directory).
    ```bash
    pnpm dev:next
    ```
    (If `dev:next` is not a script in this example's `package.json`, try `pnpm run dev`)
* This will typically start the server on `http://localhost:3000`. Keep this terminal open.

## How to Test

1.  Ensure all four components are running in their respective terminals:
    * Ollama server.
    * LiveKit server (Docker).
    * Python voice agent (`agent.py dev`).
    * Frontend example (`pnpm dev:next` or `pnpm run dev`).
2.  Open a web browser.
3.  Navigate to the voice assistant example page. You need to provide the `room` and `user` URL parameters to match your agent's configuration and assign a user identity:
    `http://<your-laptop-ip>:3000/voice-assistant?room=test-german-agent&user=YourName`
    * Replace `<your-laptop-ip>` with the IP of the machine running the frontend dev server (if accessing from another device). If on the same machine, `localhost` can be used:
    `http://localhost:3000/voice-assistant?room=test-german-agent&user=YourName`
    * Replace `YourName` with any desired user display name.
4.  Click the "Connect" button on the webpage (if present for the specific example page).
5.  Allow microphone permissions in your browser when prompted.
6.  Speak in German.
7.  **Observe**:
    * **Frontend**: UI should indicate connection and audio activity.
    * **Python Agent Terminal**: You should see detailed logs:
        * Participant joining.
        * STT processing your speech (e.g., `INFO:stt_custom:STT Transcription result: '...'`).
        * The final STT result being passed to the LLM (`INFO:agent_script:Final STT Result: '...'`).
        * The LLM's text response (e.g.,`INFO:agent_script:Final LLM Text Response: '...'`).
        * The DummyTTS receiving the text (`INFO:tts_custom:DummyTTS: Received text to synthesize: '...'`).

## Current Status & Next Steps

* **Working**:
    * LiveKit server connection.
    * VAD (Voice Activity Detection) via Silero.
    * Local STT (German, `faster-whisper` on CPU) via custom wrapper is transcribing speech.
    * Frontend connection to LiveKit server.
* **Partially Working / Next to Verify**:
    * LLM integration with local Ollama: The agent is configured to use it. Logs need to be checked for successful LLM responses.
* **To Do / Areas for Improvement**:
    * **Verify LLM Connection & Response**: Ensure Ollama receives requests and its text responses are logged correctly by the agent.
    * **Implement Real Local TTS**: Replace `DummyTTS` with a functional local TTS engine (e.g., Piper TTS, or investigate Coqui TTS Python 3.12 solutions like building from source or alternative packages) and integrate it by implementing the `livekit.agents.tts.TTS` interface for audio frame streaming.
    * **STT Audio Resampling**: The STT can receive audio at sample rates other than 16kHz (e.g., 24kHz was observed). Implement resampling in `CustomSTT` to 16kHz before passing to `faster-whisper` for optimal accuracy.
    * **STT on GPU**: Revisit running `faster-whisper` on GPU for better performance once the CPU pipeline is stable.
    * **Error Handling**: Enhance error handling and resilience in the agent and custom components.
    * **Frontend Customization**: Adapt or replace the example frontend for a more specific use case.
    * **Configuration**: Make component configurations (model paths, TTS voices, etc.) more flexible (e.g., via environment variables or a config file for the agent).
    * **Dockerize Agent**: Consider Dockerizing the Python agent and its dependencies.

## Troubleshooting Notes

* **Module Not Found (Frontend)**: If errors like `Can't resolve '@livekit/components-styles'` occur, ensure `pnpm install` and then `pnpm build` were run from the root of the `livekit-frontend-example` monorepo. Also, try clearing the `.next` cache (`rm -rf .next`) in the `examples/nextjs` directory.
* **Python Package Installation (`TTS`)**: The Coqui `TTS` package (as of June 2025 via `pip install TTS`) has shown Python version constraints incompatible with Python 3.12. This README currently uses a `DummyTTS`. Alternative TTS solutions compatible with Python 3.12 (like Piper TTS or newer Coqui distributions if available) would need their own setup steps.
* **LLM Connection Issues**: Confirm `OPENAI_API_BASE` in `agent/.env` points to your Ollama server's OpenAI-compatible endpoint (e.g., `http://localhost:11434/v1`). Ensure `agent.py` correctly initializes and uses the `AsyncOpenAI` client with this base URL. Check Ollama server logs.
* **Firewall**: Ensure your OS firewall isn't blocking local network connections to ports used by LiveKit (7880 TCP, UDP media ports like 50000-60000 or the configured range), Ollama (11434 TCP), or the frontend dev server (3000 TCP).
* **Check all terminal logs**: Each component has its own terminal output. These are crucial for debugging.
* **IP Addresses**: When using `<your-laptop-ip>` in URLs or configs, ensure it's the correct LAN IP of the host machine, reachable by other devices on the network.

---