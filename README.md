# JARVIS — Personal AI Assistant

A voice-activated, local-first personal AI assistant with persistent memory, plugin architecture, and a system tray UI. Built in Python, powered by Google Gemini.

> **Current Status: Phase 1 — Core Loop (Text-Only)**

---

## Quick Start (Phase 1)

### Prerequisites
- Python 3.11+
- A Google Gemini API key ([get one free here](https://aistudio.google.com/apikey))

### Setup

```bash
# 1. Navigate to the project
cd path/to/Jarvis

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your API key
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
# Then edit .env and paste your Gemini API key

# 5. Run JARVIS
python main.py
```

### Usage

Once running, you'll see the JARVIS prompt. Just type naturally:

```
  Sir > What time is it?

  JARVIS: It's Friday, July 18, 2026 at 10:45:23 AM.

  Sir > Explain quantum computing in one sentence.

  JARVIS: Quantum computing uses quantum-mechanical phenomena like superposition
  and entanglement to process information in ways classical computers cannot.

  Sir > quit

  JARVIS: Until next time, Sir.
```

**Commands:**
- `quit` / `exit` — End the session
- `clear` — Reset conversation history
- `Ctrl+C` — Force quit

### Configuration

| File | Purpose |
|---|---|
| `.env` | API keys and secrets (gitignored) |
| `config/settings.yaml` | Model, memory, logging settings |
| `config/personality.md` | JARVIS personality and behavior rules |

Edit `config/settings.yaml` to change the model, temperature, or your name. Edit `config/personality.md` to change how JARVIS talks.

---

## Project Structure

```
Jarvis/
├── core/
│   ├── brain.py       # LLM interface (Gemini + tool-calling)
│   ├── config.py      # Config loader (.env + YAML)
│   └── logger.py      # Structured logging
├── memory/
│   └── buffer.py      # Rolling conversation buffer
├── plugins/
│   └── _template.py   # Plugin template for Phase 4
├── config/
│   ├── settings.yaml  # Main settings
│   └── personality.md # System prompt
├── ui/                # Phase 6
├── main.py            # Entry point
├── .env.example       # Secrets template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Roadmap

- [x] **Phase 1** — Core loop (text-only CLI chat, Gemini brain, tool-calling)
- [ ] **Phase 2** — Voice I/O (wake word, STT, TTS)
- [ ] **Phase 3** — Memory (vector store, remember/recall/forget)
- [ ] **Phase 4** — Plugin architecture (filesystem, apps, calendar, email, etc.)
- [ ] **Phase 5** — Safety rails (confirmations, rate limits, credential security)
- [ ] **Phase 6** — UI (system tray, web dashboard)
- [ ] **Phase 7** — Polish (personality, proactive behavior, visual HUD)
