# Cloud Testing Setup Guide

## ☁️ Run Everything on GitHub (Zero Local Setup!)

Your AI Research System can run entirely on GitHub's infrastructure with no local dependencies.

### Step 1: Add Your API Key to GitHub Secrets

1. Go to your repository: https://github.com/ronit111/ai-research-system
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add the secret:
   - **Name**: `ANTHROPIC_API_KEY`
   - **Value**: Your Anthropic API key (starts with `sk-ant-`)
6. Click **Add secret**

### Step 2: Run Tests on GitHub

**Option A: Automatic (on every push)**
- Just push code to `main` branch
- Tests run automatically
- View results in the **Actions** tab

**Option B: Manual Trigger**
1. Go to **Actions** tab
2. Click **AI Research System Tests** (left sidebar)
3. Click **Run workflow** button (right side)
4. Select `main` branch
5. Click **Run workflow**

### Step 3: View Results

1. Click on the running workflow
2. Watch real-time logs as agents execute
3. See test results and cost summaries
4. Download artifacts (database, Obsidian notes)

## 🎯 What Gets Tested

- ✅ **Agent 1**: Literature Review (5 papers)
- ✅ **Agent 2**: Idea Generation (5 ideas)
- ✅ **Full 6-Agent Workflow**: Complete research cycle

## 💰 Cost

- Each test run: ~$0.50-1.00
- Runs on GitHub's servers (free for public repos)
- Cost tracking included in artifacts

## 📊 Artifacts

After each run, download:
- `data/research.db` - Complete database
- `data/costs.json` - Cost breakdown
- Obsidian vault with all generated notes

## 🔒 Security

- API key stored as encrypted GitHub Secret
- Never exposed in logs or artifacts
- Only accessible to workflow runs

---

**No local Python, no virtual environments, no installations needed!** ☁️
