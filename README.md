# Broke

Multi-agent portfolio system. An AI-powered conversational agent that answers questions about Jonathan Caudill — skills, experience, projects, and culture fit.

## Quick Start

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install
pip install -e .

# Configure (copy and edit)
cp .env.example .env

# Run
broke
```

## Configuration

Copy `.env.example` to `.env` and set your model:

- **Ollama (local):** `BROKE_MODEL=ollama/llama3.1`
- **LM Studio:** `BROKE_MODEL=openai/local-model` + `BROKE_LLM_BASE_URL=http://localhost:1234/v1`
- **OpenAI:** `BROKE_MODEL=openai/gpt-4o` + `OPENAI_API_KEY=sk-...`

## Architecture

An orchestrator agent receives user queries, dispatches specialist agents asynchronously, and streams responses back in real time.

**Specialists:** skills, experience, projects, culture fit — each with RAG access to the knowledge base and the ability to call other agents peer-to-peer.

## Commands

- `/debug` — toggle debug mode (shows routing decisions)
- `/clear` — reset conversation history
- `/quit` — exit

## Knowledge Base

Edit the markdown files in `knowledge_data/` to update the agent's knowledge. They are automatically ingested into ChromaDB on startup.
