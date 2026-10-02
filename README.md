# VoxFlow AI

## Desktop application

The desktop interface is a PySide6 application. Install the project dependencies, then
launch it from the project directory:

```bash
python -m pip install -r requirements.txt
python main.py
```

The interface records mono WAV audio through Qt Multimedia, passes its temporary file
to `process_audio(audio_file_path)`, and plays returned MP3 bytes through Qt Multimedia.
Allow microphone access in your operating system settings. PySide6 supplies both the
widgets and the Qt Multimedia audio capture and playback components.

The main window is implemented in `main.py`; recording and WAV file creation live in
`audio_recorder.py`. Backend configuration still comes from the existing `.env` values.

VoxFlow AI is a desktop voice-enabled AI assistant built with Python, LangGraph, Gemini, and ElevenLabs.

The project is intentionally small and focused. The goal is to build a clean voice-agent workflow in one day while demonstrating:

- LLM integration
- LangGraph state and routing
- Tool calling
- Speech-to-Text
- Text-to-Speech
- Text-only fallback for responses that should not be spoken
- Simple persistent tools

## Core Workflow

The application should work like this:

```text
User speaks
    ↓
Audio input
    ↓
ElevenLabs Speech-to-Text
    ↓
user_text
    ↓
LangGraph Router
    ↓
RouterDecision
    ↓
┌───────────────────────────────┐
│ route = "tool" or "llm"       │
│ response_mode = text/speech   │
│ selected_tool = tool or None  │
└───────────────────────────────┘
    ↓
```

The router decides two separate things:

1. Who should handle the request?
   - `tool`
   - `llm`

2. How should the final answer be returned?
   - `speech`
   - `text`

These decisions are independent.

For example:

```text
"What time is it?"

route = "tool"
selected_tool = "datetime"
response_mode = "speech"
```

```text
"Explain recursion simply."

route = "llm"
selected_tool = None
response_mode = "speech"
```

```text
"Write DFS implementation in Python."

route = "llm"
selected_tool = None
response_mode = "text"
```

The DFS implementation should be displayed in the desktop UI and should not be converted to speech.

---

## LangGraph State

The shared graph state is defined in `state.py`.

```python
class AgentState(TypedDict):
    user_text: str
    route: str
    response_mode: str
    selected_tool: str | None
    response_text: str
```

The router uses structured output:

```python
class RouterDecision(BaseModel):
    route: Literal["tool", "llm"]
    response_mode: Literal["text", "speech"]
    selected_tool: Literal[
        "calculator",
        "datetime",
        "save_note",
        "get_notes"
    ] | None
```

---

## Available Tools

The first version contains only simple local tools.

### Calculator

Used for arithmetic requests.

Example:

```text
"Calculate 245 * 18"
```

Tool:

```python
calculator(...)
```

---

### Date and Time

Used when the user asks for the current date or time.

Example:

```text
"What time is it?"
```

Tool:

```python
get_current_datetime()
```

---

### Save Note

Stores a note locally.

Example:

```text
"Remember that my interview is Friday."
```

Tool:

```python
save_note(...)
```

Notes should be persisted locally, for example in a JSON file.

---

### Get Notes

Returns previously stored notes.

Example:

```text
"What did I ask you to remember?"
```

Tool:

```python
get_notes()
```

---

## Unsupported Tool Requests

The assistant must not pretend that unavailable actions exist.

For example:

```text
"Send an email to John."
```

There is no email tool.

The assistant should return something similar to:

```text
I don't currently have a tool for sending emails.
```

It must not simulate or claim that the email was sent.

---

## Graph Logic

The intended LangGraph flow is:

```text
START
  ↓
router_node
  ↓
route?
  ├── tool
  │     ↓
  │  tool_node
  │     ↓
  │  response_node
  │
  └── llm
        ↓
     response_node
        ↓
response_mode?
  ├── speech → ElevenLabs TTS
  └── text   → UI only
        ↓
       END
```

Important:

ElevenLabs Speech-to-Text and Text-to-Speech do not need to be LangGraph nodes.

The graph is responsible mainly for:

- routing
- tool selection
- LLM execution
- response generation

The desktop application handles:

- microphone input
- audio recording
- STT
- displaying text
- playing generated speech

---

## Tool Result Flow

Tool results should normally be returned to the LLM before producing the final user-facing response.

Example:

```text
User:
"What time is it?"

Router:
tool = datetime

Tool:
"2026-10-01 15:45"

LLM:
"It's currently 3:45 PM."

ElevenLabs TTS:
generates spoken response
```

This makes responses natural instead of directly speaking raw tool output.

---

## Tech Stack

```text
Language        Python
Desktop UI      PySide6
Workflow        LangGraph
LLM             Gemini API
STT             ElevenLabs
TTS             ElevenLabs
Local storage   JSON
```

---

## Planned Project Structure

```text
voxflow-ai/
│
├── app.py
├── graph.py
├── state.py
├── prompts.py
│
├── nodes/
│   ├── router.py
│   ├── responder.py
│   └── tool_executor.py
│
├── tools/
│   ├── calculator.py
│   ├── datetime_tool.py
│   └── notes.py
│
├── services/
│   ├── gemini.py
│   ├── stt.py
│   └── tts.py
│
├── data/
│   └── notes.json
│
├── .env
├── requirements.txt
└── README.md
```

---

## Development Principles

Keep the first version simple.

Do not add:

- RAG
- MCP
- database infrastructure
- authentication
- multiple agents
- realtime streaming
- WebSockets
- image generation
- complex memory systems

The goal is to finish a small, clean, working Voice AI Agent with understandable LangGraph routing.

Every component should remain simple enough to explain during an interview.
