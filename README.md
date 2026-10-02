# VoxFlow AI

VoxFlow AI is a voice-enabled desktop assistant built with Python, PySide6, LangGraph, Gemini, and ElevenLabs. Speak into the microphone and the app transcribes the recording, routes the request through a small agent workflow, runs a local tool or generates an answer, and returns text with optional speech playback.

This is a portfolio project focused on the backend design: a clear LangGraph workflow, structured request routing, tool execution, and the integration of speech-to-text and text-to-speech services. The desktop interface makes the system usable, but its current UI/UX is intentionally modest and has significant room for improvement. The main goal was to demonstrate the voice-agent architecture and backend workflow in a small, understandable application.

## What it does

- Records microphone input in the PySide6 desktop app and saves it as a temporary WAV file.
- Transcribes speech with ElevenLabs Speech-to-Text (Scribe v2).
- Uses Gemini to classify each request and choose a response mode: speech or text.
- Routes supported actions to local tools: arithmetic, current local time, and JSON-backed notes.
- Uses Gemini to turn tool results into a clear response, or answer requests that do not need a tool.
- Generates spoken replies with ElevenLabs Text-to-Speech when the selected response mode is speech.
- Displays the recognized request and response in the desktop interface; generated audio can be played there.

Unsupported actions are not simulated. If the assistant has no tool for a requested action, it should say so instead of claiming it completed the action.

## How a request flows

```text
Microphone
    ↓
Qt records a temporary WAV file
    ↓
ElevenLabs Speech-to-Text
    ↓
LangGraph router (Gemini structured output)
    ├── route = "tool" → local tool executor ─┐
    └── route = "llm" ────────────────────────┤
                                              ↓
                                   Gemini response node
                                              ↓
                            response_text + response_mode
                              ├── speech → ElevenLabs TTS → audio playback
                              └── text   → display in the UI
```

The router returns the route, response mode, selected tool, and tool input. The tool executor returns a raw tool result. The responder uses the original request and, when present, that result to produce the final user-facing response. Speech recognition and synthesis are handled by the desktop/backend boundary rather than being modeled as LangGraph nodes.

## Tools

| Tool | What it does |
| --- | --- |
| `calculator` | Evaluates basic arithmetic expressions safely, without Python `eval`. |
| `datetime` | Returns the current local time. |
| `save_note` | Saves a note locally in `data/notes.json`. The file and directory are created on first use. |
| `get_notes` | Returns the saved notes. |

The datetime tool currently returns the time, not the calendar date. Notes are simple local JSON storage, not a searchable memory system.

## Technology

- **Language:** Python
- **Desktop UI and audio capture/playback:** PySide6 and Qt Multimedia
- **Workflow orchestration:** LangGraph
- **LLM:** Gemini through LangChain Google GenAI
- **Speech-to-text and text-to-speech:** ElevenLabs
- **Notes storage:** local JSON file

## Setup

Use Python and PowerShell from the project directory on Windows.

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

If PowerShell does not allow activation scripts, run the virtual environment's Python directly:

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe main.py
```

Allow desktop microphone access in Windows privacy settings and choose a working input device in Windows Sound settings.

## Configuration

Create a `.env` file in the project root with the API keys used by the services:

```dotenv
GOOGLE_API_KEY=your_google_ai_studio_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

The application loads these values through `python-dotenv`. Keep `.env` private; it is ignored by Git. Requests that use Gemini or ElevenLabs require valid credentials and network access.

## Project structure

```text
VoxFlowAI/
├── app.py                    # STT → graph → optional TTS application boundary
├── audio_recorder.py         # Qt microphone capture and temporary WAV lifecycle
├── main.py                   # PySide6 desktop UI and background processing worker
├── graph.py                  # LangGraph nodes, edges, routing, and compilation
├── state.py                  # Graph state and structured router decision
├── prompts.py                # Router and responder system prompts
├── nodes/
│   ├── router.py             # Gemini structured request routing
│   ├── tool_executor.py      # Dispatches supported local tools
│   └── responder.py          # Produces the final user-facing answer
├── tools/
│   ├── calculator.py
│   ├── datetime_tool.py
│   └── notes.py
├── services/
│   ├── gemini.py
│   ├── stt.py
│   └── tts.py
├── requirements.txt
└── README.md
```

## Current scope

VoxFlow AI is deliberately a small, explainable first version. It demonstrates routing and tool use in one LangGraph workflow, plus a voice input/output pipeline. It does not include RAG, databases, authentication, external action tools, multi-agent orchestration, or realtime streaming. The UI is a functional shell for this backend-focused portfolio project, not a claim that the product experience is finished.
