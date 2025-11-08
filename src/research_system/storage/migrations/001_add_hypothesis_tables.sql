-- Database Migration: Add Tables for Agents 3-6
-- Version: 001
-- Date: 2025-11-08
-- Description: Adds hypotheses, experiment_designs, experiment_runs, and analyses tables

-- =============================================================================
-- HYPOTHESES TABLE (Agent 3 output)
-- =============================================================================
CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT PRIMARY KEY,                    -- UUID
    project_id TEXT NOT NULL,               -- Foreign key to projects
    idea_id TEXT,                           -- Source idea (optional)
    title TEXT NOT NULL,                    -- Hypothesis title
    null_hypothesis TEXT NOT NULL,          -- H0 statement
    alternative_hypothesis TEXT NOT NULL,   -- H1 statement
    independent_vars TEXT NOT NULL,         -- JSON array
    dependent_vars TEXT NOT NULL,           -- JSON array
    control_vars TEXT,                      -- JSON array
    metrics TEXT NOT NULL,                  -- JSON array of metric specs
    statistical_tests TEXT,                 -- JSON array of test names
    status TEXT DEFAULT 'formulated',       -- formulated, tested, validated, rejected
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT,                          -- JSON for additional fields
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_hypotheses_project ON hypotheses(project_id);
CREATE INDEX IF NOT EXISTS idx_hypotheses_status ON hypotheses(status);
CREATE INDEX IF NOT EXISTS idx_hypotheses_idea ON hypotheses(idea_id);

-- =============================================================================
-- EXPERIMENT DESIGNS TABLE (Agent 4 output)
-- =============================================================================
CREATE TABLE IF NOT EXISTS experiment_designs (
    id TEXT PRIMARY KEY,                    -- UUID
    project_id TEXT NOT NULL,
    hypothesis_id TEXT NOT NULL,            -- Foreign key to hypotheses
    title TEXT NOT NULL,
    methodology TEXT NOT NULL,              -- Detailed methodology description
    datasets TEXT NOT NULL,                 -- JSON array of dataset specs
    baselines TEXT NOT NULL,                -- JSON array of baseline specs
    code_scaffold TEXT,                     -- Generated code template
    resource_estimates TEXT NOT NULL,       -- JSON: {compute, time_hours, cost_usd}
    status TEXT DEFAULT 'designed',         -- designed, ready, archived
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
);

CREATE INDEX IF NOT EXISTS idx_designs_project ON experiment_designs(project_id);
CREATE INDEX IF NOT EXISTS idx_designs_hypothesis ON experiment_designs(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_designs_status ON experiment_designs(status);

-- =============================================================================
-- EXPERIMENT RUNS TABLE (Agent 5 output)
-- =============================================================================
CREATE TABLE IF NOT EXISTS experiment_runs (
    id TEXT PRIMARY KEY,                    -- UUID
    project_id TEXT NOT NULL,
    design_id TEXT NOT NULL,                -- Foreign key to experiment_designs
    platform TEXT NOT NULL,                 -- kaggle, modal, local
    platform_run_id TEXT,                   -- Platform-specific run ID
    status TEXT DEFAULT 'pending',          -- pending, running, completed, failed
    started_at TEXT,
    completed_at TEXT,
    duration_seconds REAL,
    results TEXT,                           -- JSON: metrics, outputs, artifacts
    logs TEXT,                              -- Execution logs
    error TEXT,                             -- Error message if failed
    cost_usd REAL DEFAULT 0.0,              -- Actual execution cost
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (design_id) REFERENCES experiment_designs(id)
);

CREATE INDEX IF NOT EXISTS idx_runs_project ON experiment_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_runs_design ON experiment_runs(design_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON experiment_runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_platform ON experiment_runs(platform);

-- =============================================================================
-- ANALYSES TABLE (Agent 6 output)
-- =============================================================================
CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,                    -- UUID
    project_id TEXT NOT NULL,
    run_id TEXT NOT NULL,                   -- Foreign key to experiment_runs
    hypothesis_id TEXT,                     -- Original hypothesis
    statistical_results TEXT NOT NULL,      -- JSON: test results, p-values, etc.
    baseline_comparisons TEXT,              -- JSON: comparisons to baselines
    visualizations TEXT,                    -- JSON array of file paths
    insights TEXT NOT NULL,                 -- Key insights and findings
    conclusions TEXT NOT NULL,              -- Conclusions about hypothesis
    next_steps TEXT,                        -- JSON array of recommendations
    status TEXT DEFAULT 'completed',        -- completed, archived
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (run_id) REFERENCES experiment_runs(id),
    FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
);

CREATE INDEX IF NOT EXISTS idx_analyses_project ON analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_analyses_run ON analyses(run_id);
CREATE INDEX IF NOT EXISTS idx_analyses_hypothesis ON analyses(hypothesis_id);

-- =============================================================================
-- CHECKPOINTS TABLE (for resumable experiments)
-- =============================================================================
CREATE TABLE IF NOT EXISTS experiment_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    step TEXT NOT NULL,                     -- Current execution step
    partial_results TEXT,                   -- JSON of partial results
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES experiment_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_run ON experiment_checkpoints(run_id);

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these to verify migration success:

-- Check table creation
-- SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Check indexes
-- SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;

-- Test insertion (remove -- to test)
-- INSERT INTO hypotheses (id, project_id, title, null_hypothesis, alternative_hypothesis, independent_vars, dependent_vars, metrics, created_at, updated_at)
-- VALUES ('test_123', 'test_project', 'Test Hypothesis', 'H0: No effect', 'H1: Significant effect', '["var1"]', '["var2"]', '[]', datetime('now'), datetime('now'));

-- SELECT * FROM hypotheses WHERE id = 'test_123';
-- DELETE FROM hypotheses WHERE id = 'test_123';
