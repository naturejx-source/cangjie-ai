# Cangjie AI 倉頡 AI

> A locally-deployed Cantonese AI assistant for Hong Kong solo founders — legal, admin, and compliance guidance in 5 language modes.

## Overview

Cangjie AI runs on local Ollama (Llama 3) and provides step-by-step guidance for Hong Kong business registration, compliance, and cross-border admin workflows. No data leaves your machine.

**Tech Stack**: Python + Ollama + Llama 3

## Language Modes

| Mode | Description |
|------|-------------|
| `hk` | Hong Kong written Chinese |
| `yue` | Spoken Cantonese style |
| `en` | English only |
| `zh-Hant` | Neutral Traditional Chinese |
| `zh-Hans` | Simplified (lowest priority, only on request) |

## Usage

```bash
python cangjie_agent.py
python cangjie_agent.py --model llama3.1 --lang yue
python cangjie_agent.py --log
```

## Commands

- `/lang hk|yue|en|zh-Hant|zh-Hans` — Switch language
- `/help` — Show help
- `/clear` — Clear memory
- `/exit` — Quit

## Voice Lore

Place `.txt` or `.md` files in `cangjie_flavor/` to inject Hong Kong cultural context into the AI responses.

## Requirements

- Python 3.8+
- Ollama running locally (`ollama serve`)
- `ollama pull llama3`

## Author

**WU, JINXIA (Rucia Woo)** — BSc Software Engineering | Cantonese AI Explorer
