# Local Open-Source Voice Agent with LiveKit

This project demonstrates a locally runnable voice agent pipeline using LiveKit for real-time communication, local Speech-to-Text (STT) with `faster-whisper`, a local Large Language Model (LLM) via Ollama, and a placeholder for Text-to-Speech (TTS). The primary goal is to understand how these components work together.

## Current Features

* **LiveKit Server**: Self-hosted for managing WebRTC sessions.
* **Local STT**: Custom `faster-whisper` integration for German speech-to-text (runs on CPU).
    * Includes automatic audio resampling from various input sample rates to the required 16kHz for high accuracy.
* **Local LLM**: Confirmed working integration with Ollama (e.g., with the `mistral` model) for text generation, accessed via an OpenAI-compatible API.
* **Python Agent**: `livekit-agents` based Python application that orchestrates a full VAD-STT-LLM pipeline.
* **Web Frontend**: A Next.js example from `livekit/components-js` for interacting with the agent.
* **Text-based Interaction**: The agent reliably processes voice to text and gets a text response from the LLM, which is logged to the console.

## Prerequisites

Ensure you have the following software installed on your system (primarily tested on Linux, e.g., Ubuntu/Mint):

1.  **Docker & Docker Compose**: For running the LiveKit server.
    * [Install Docker](https://docs.docker.com/engine/install/)
    * [Install Docker Compose](https://docs.docker.com/compose/install/)
2.  **Python**: Version 3.12.x is used in this project.
    * Check with: `python3 --version`
    * Check with: `pip --version`
    * Ensure the `python3-venv` package (or equivalent for your Python version) is installed (e.g., `sudo apt install python3.12-venv` on Debian/Ubuntu).
3.  **Node.js and pnpm**: For running the frontend example.
    * Node.js (e.g., v18+ recommended): Check with `node --version`
    * npm (comes with Node.js): Check with `npm --version`
    * pnpm: Install globally with `sudo npm install -g pnpm`
4.  **Ollama**: For running local LLMs.
    * [Install Ollama](https://ollama.com/download)
5.  **Git**: For version control and cloning repositories.
6.  **Build Essentials & CMake**:
    * Install with: `sudo apt install build-essential cmake`

## Directory Structure

(Assuming this `README.md` is at the root of the `voice-agents` project directory)

```text
./
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
```
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
    Your `requirements.txt` should look like this:
    ```txt
    livekit-agents[openai,silero,turn-detector]
    python-dotenv
    requests
    faster-whisper
    numpy
    resampy
    ```
    Install with:
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
* Keep this terminal open.

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
    * **Important**: Replace `<your-laptop-ip>` with the actual Local Area Network (LAN) IP address of the machine running the LiveKit server. On Linux, find this with `ip addr show`. Do **not** use `localhost` or `127.0.0.1` for this variable if you intend to test the frontend from *other devices* on your network.
* **Run the frontend development server**:
    The command `pnpm dev:next` (which runs `turbo run dev --filter=@livekit/component-example-next...`) worked for you previously. If that script doesn't exist, `pnpm run dev` is the standard fallback.
    ```bash
    pnpm dev:next
    ```
* This will start the server on `http://localhost:3000`. Keep this terminal open.

## How to Test

1.  Ensure all four components are running in their respective terminals.
2.  Open a web browser.
3.  Navigate to the voice assistant example page, providing the `room` and `user` URL parameters:
    `http://<your-laptop-ip>:3000/voice-assistant?room=test-german-agent&user=YourName`
    *(If accessing from the same machine where the frontend is running, you can use `localhost` in place of `<your-laptop-ip>`)*
4.  Click the "Connect" button (if present).
5.  Allow microphone permissions in your browser.
6.  Speak in German.
7.  **Observe**: In the Python Agent Terminal, you should see a clean sequence of logs showing your speech being transcribed, sent to the LLM, and the final text response from the LLM being logged.

## Current Status & Next Steps

* **Working**:
    * VAD-STT-LLM text pipeline is stable and functional.
    * Local STT with `faster-whisper` provides accurate transcription thanks to audio resampling.
    * Local LLM with Ollama is successfully integrated and responsive.
    * Custom agent components (`CustomSTT`, `DummyTTS`) correctly implement the necessary `livekit-agents` interfaces to prevent crashes.
* **Next Steps / To Do**:
    * **Implement Real Local TTS**: This is the top priority. Replace `DummyTTS` with a functional local TTS engine (e.g., Piper TTS) to make the agent speak.
    * **GPU Acceleration**: Revisit running STT and LLM on the GPU to improve performance and reduce CPU load.
    * **Frontend Improvements**: Display the conversation (transcripts and LLM responses) in the web UI.
    * **Configuration**: Make component settings like model names and paths more flexible.
    * **Dockerize Agent**: Consider Dockerizing the Python agent for easier deployment.

## Troubleshooting Notes

* **Module Not Found (Frontend)**: If errors like `Can't resolve '@livekit/components-styles'` occur, ensure `pnpm install` and then `pnpm build` were run from the root of the `livekit-frontend-example` monorepo. Also, try clearing the `.next` cache (`rm -rf .next`) in the `examples/nextjs` directory.
* **Python Version Incompatibilities**: Some libraries (like Coqui `TTS`) may have strict Python version requirements. This project was developed with Python 3.12.
* **IP Addresses**: When using `<your-laptop-ip>` in URLs or configs, ensure it's the correct LAN IP of the host machine, reachable by other devices on the network.