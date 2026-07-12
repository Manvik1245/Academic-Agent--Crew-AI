# Academic-Agent--Crew-AI

A highly specialized, multi-agent orchestration framework built to automate academic research, note synthesis, and software development workflows. This project leverages **CrewAI** for autonomous agent coordination and **Gemini Flash 3.5** for high-throughput, low-latency reasoning.

---

## 🏗️ Technical Stack

- **Orchestration:** [CrewAI](https://www.crewai.com/) for multi-agent delegation and task sequencing.
- **LLM Engine:** Gemini Flash 3.5 via OpenRouter.
- **Environment Management:** [uv](https://github.com/astral-sh/uv) for high-performance dependency management and project scaffolding.
- **Language:** Python 3.12+

---

## 🚀 Core Capabilities

### 1. Notion Data Integration
The system implements a custom `notion_connection` tool designed to interface with the Notion API dynamically.
- **Dynamic Property Mapping:** Automatically discovers database schema properties of type `title` to ensure accurate document retrieval regardless of column naming.
- **Contextual Retrieval:** Bridges the gap between raw API JSON responses and agent-readable text, allowing the agent to perform RAG (Retrieval-Augmented Generation) on personal class notes and lecture materials.

### 2. Autonomous Coding & Orchestration
The agentic framework is structured to assist in software engineering tasks, specifically focusing on local development support.
- **Custom Tool Creation:** Utilizes `crewai.tools` to extend agent capabilities, enabling the creation of bespoke tools for local file manipulation, script debugging, and data processing.
- **Multi-Agent Orchestration:** Deploys specialized agents to break down complex coding prompts into actionable workflows, managing task dependencies and sub-task delegation within the crew.



---

## 🛠️ Setup & Execution

### Prerequisites
- Python 3.12+
- `uv` installed (`pip install uv`)
- API Keys: `NOTION_API_TOKEN`, `NOTION_DATABASE_ID`, `GEMINI_API_KEY` (configured in a local `.env` file)

### Installation
```bash
# Sync dependencies via uv
uv sync

To initialize the orchestration loop:
uv run python main.py

