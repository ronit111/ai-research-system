# Quick Start Guide

Get your AI Research System running in 5 minutes!

## Prerequisites

- Python 3.11 or higher
- Anthropic API key (get from https://console.anthropic.com/)

## Setup

### 1. Navigate to Project

```bash
cd "/Users/ronitchidara/Library/CloudStorage/OneDrive-Personal/Obsidian-Vault/Second Brain/ai-research-system"
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

If you get errors, install individually:
```bash
pip install anthropic requests pandas pydantic pydantic-settings python-dotenv
```

### 4. Configure API Key

Edit the `.env` file (it's already in the project):

```bash
nano .env
```

Replace `your_api_key_here` with your actual Anthropic API key, then save (Ctrl+X, Y, Enter).

## Test Agent 1

Run the Literature Review Agent:

```bash
python scripts/test_agent1.py
```

This will:
- Search for papers on "attention mechanisms in transformers"
- Score relevance using Claude
- Save papers to database
- Create summaries in your Obsidian vault
- Display results and cost

**Expected output:**
- 3 relevant papers found
- Summaries saved to `AI-Research/Papers/`
- Total cost: ~$0.05-0.15

## What Just Happened?

1. **Semantic Scholar Search**: Queried 200M+ papers
2. **Claude Scoring**: Rated each paper's relevance (1-10)
3. **Database Storage**: Saved papers to SQLite
4. **Obsidian Integration**: Created markdown notes in your vault
5. **Cost Tracking**: Logged API usage and costs

## Next Steps

### View Results in Obsidian

Open Obsidian and navigate to:
```
AI-Research/Papers/
```

You'll see 3 new paper summaries!

### Check Cost Tracking

```bash
python -c "from src.research_system.services.cost_tracker import cost_tracker; cost_tracker.print_monthly_report()"
```

### Run Custom Query

Edit `scripts/test_agent1.py` and change line 19:
```python
query = "your research topic here"
```

Then run again:
```bash
python scripts/test_agent1.py
```

## Troubleshooting

### Error: "No module named 'anthropic'"

```bash
pip install anthropic
```

### Error: "API key not found"

Make sure you edited `.env` with your real API key.

### Error: "Cannot create directory"

Check that the Obsidian vault path in `.env` is correct.

## What's Built So Far

✅ **Foundation (Week 1)**
- Base agent framework
- Cost tracking system
- SQLite database
- Workflow orchestrator

✅ **Agent 1: Literature Review**
- Semantic Scholar integration (200M+ papers)
- Relevance scoring with Claude
- Obsidian vault integration
- Knowledge graph ready (structure in place)

🚧 **Coming Next**
- Agent 2: Idea Generation
- Agent 3: Hypothesis Formation
- Agent 4: Experiment Design
- Agent 5: Execution
- Agent 6: Analysis

## Questions?

Check:
- Main README.md for architecture details
- pyproject.toml for dependencies
- src/research_system/ for code

Happy researching! 🚀
