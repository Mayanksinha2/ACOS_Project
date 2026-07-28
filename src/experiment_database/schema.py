from __future__ import annotations

SCHEMA_VERSION = 1

CREATE_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    description TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    variant_name TEXT NOT NULL,
    repetition_index INTEGER NOT NULL,
    random_seed INTEGER,
    status TEXT NOT NULL,
    successful INTEGER NOT NULL,
    reward REAL,
    duration_seconds REAL,
    conflict_detected INTEGER NOT NULL DEFAULT 0,
    negotiation_required INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    errors_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY (experiment_id)
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_runs_experiment_id
    ON runs(experiment_id);

CREATE INDEX IF NOT EXISTS idx_runs_variant_name
    ON runs(variant_name);

CREATE INDEX IF NOT EXISTS idx_runs_reward
    ON runs(reward);

CREATE INDEX IF NOT EXISTS idx_runs_created_at
    ON runs(created_at);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    run_id TEXT,
    artifact_type TEXT NOT NULL,
    path TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (experiment_id)
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    FOREIGN KEY (run_id)
        REFERENCES runs(run_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_artifacts_experiment_id
    ON artifacts(experiment_id);

CREATE INDEX IF NOT EXISTS idx_artifacts_run_id
    ON artifacts(run_id);

CREATE TABLE IF NOT EXISTS reports (
    report_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    run_id TEXT,
    markdown_path TEXT,
    html_path TEXT,
    manifest_path TEXT,
    data_path TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (experiment_id)
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    FOREIGN KEY (run_id)
        REFERENCES runs(run_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_experiment_id
    ON reports(experiment_id);

CREATE TABLE IF NOT EXISTS publications (
    publication_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    run_id TEXT,
    markdown_path TEXT,
    latex_path TEXT,
    manifest_path TEXT,
    data_path TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (experiment_id)
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    FOREIGN KEY (run_id)
        REFERENCES runs(run_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_publications_experiment_id
    ON publications(experiment_id);

CREATE TABLE IF NOT EXISTS aggregated_evaluations (
    evaluation_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    groups_json TEXT NOT NULL DEFAULT '{}',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    errors_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY (experiment_id)
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_evaluations_experiment_id
    ON aggregated_evaluations(experiment_id);

CREATE TABLE IF NOT EXISTS ablation_results (
    ablation_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    baseline_group TEXT NOT NULL,
    primary_metric TEXT NOT NULL,
    best_group TEXT,
    worst_group TEXT,
    ranking_json TEXT NOT NULL DEFAULT '[]',
    comparisons_json TEXT NOT NULL DEFAULT '[]',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    errors_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY (experiment_id)
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ablation_experiment_id
    ON ablation_results(experiment_id);
"""
