# AI Research System

Domain-agnostic AI research automation system that takes you from research question to analysis.

## Quick Start

### 1. Setup

```bash
# Clone or navigate to the project
cd ai-research-system

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -e .
```

### 2. Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env and add your API keys
nano .env
```

Required:
- `ANTHROPIC_API_KEY`: Get from https://console.anthropic.com/

### 3. Run Your First Research

```bash
# Run literature review
python scripts/run_research.py "attention mechanisms in transformers" --papers 5
```

## Architecture

```
ai-research-system/
├── src/research_system/    # Main package
│   ├── agents/             # 6 research agents
│   ├── workflows/          # LangGraph orchestration
│   ├── storage/            # Database & file management
│   ├── services/           # Shared services
│   └── config/             # Configuration
├── data/                   # Local data storage
├── obsidian-vault/         # Obsidian integration
└── scripts/                # CLI scripts
```

## Features

- **6 Automated Agents**: Literature Review → Idea Generation → Hypothesis → Experiment Design → Execution → Analysis
- **Domain-Agnostic**: Works for ML, Biology, Physics, Social Sciences, etc.
- **Cost-Controlled**: Built-in budget tracking and alerts
- **Knowledge Graph**: Automatically builds relationships between papers and concepts
- **Obsidian Integration**: All outputs saved to your Obsidian vault

## Development Status

- [x] Phase 0: Foundation (Week 1)
- [ ] Phase 1: MVP (Weeks 2-4)
- [ ] Phase 2: Production (Weeks 5-8)

## License

MIT License - Built with Claude Code
