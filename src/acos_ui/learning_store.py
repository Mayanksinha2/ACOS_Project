from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .outcome_models import (
    MetricChange,
    OutcomeEvaluation,
    OutcomeMetrics,
)


class PersistentLearningStore:
    """
    Small persistent feedback store for the Streamlit learning workflow.

    Default location:
        <project-root>/data/acos_learning.db

    Override with:
        ACOS_LEARNING_DB
    """

    SCHEMA_VERSION = 1

    def __init__(
        self,
        database_path: str | Path | None = None,
    ) -> None:
        self.database_path = Path(
            database_path
            or os.environ.get("ACOS_LEARNING_DB")
            or self.default_database_path()
        )
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.initialize()

    @staticmethod
    def default_database_path() -> Path:
        project_root = Path(__file__).resolve().parents[2]
        return project_root / "data" / "acos_learning.db"

    def initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS learning_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS outcome_evaluations (
                    evaluation_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    experiment_id TEXT,
                    product_id TEXT NOT NULL,
                    winning_agent TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    primary_operation TEXT NOT NULL,
                    primary_value REAL NOT NULL,
                    primary_unit TEXT NOT NULL,
                    reward REAL NOT NULL,
                    classification TEXT NOT NULL,
                    successful INTEGER NOT NULL,
                    before_json TEXT NOT NULL,
                    after_json TEXT NOT NULL,
                    changes_json TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    run_snapshot_json TEXT NOT NULL,
                    evaluated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_outcome_run
                ON outcome_evaluations(run_id);

                CREATE INDEX IF NOT EXISTS idx_outcome_agent
                ON outcome_evaluations(winning_agent);

                CREATE INDEX IF NOT EXISTS idx_outcome_operation
                ON outcome_evaluations(primary_operation);

                CREATE INDEX IF NOT EXISTS idx_outcome_time
                ON outcome_evaluations(evaluated_at);
                """
            )
            connection.execute(
                """
                INSERT INTO learning_metadata(key, value)
                VALUES ('schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (str(self.SCHEMA_VERSION),),
            )
            connection.commit()

    def save(
        self,
        evaluation: OutcomeEvaluation,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO outcome_evaluations (
                    evaluation_id,
                    run_id,
                    experiment_id,
                    product_id,
                    winning_agent,
                    decision_type,
                    primary_operation,
                    primary_value,
                    primary_unit,
                    reward,
                    classification,
                    successful,
                    before_json,
                    after_json,
                    changes_json,
                    notes,
                    run_snapshot_json,
                    evaluated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evaluation.evaluation_id,
                    evaluation.run_id,
                    evaluation.experiment_id,
                    evaluation.product_id,
                    evaluation.winning_agent,
                    evaluation.decision_type,
                    evaluation.primary_operation,
                    evaluation.primary_value,
                    evaluation.primary_unit,
                    evaluation.reward,
                    evaluation.classification,
                    1 if evaluation.successful else 0,
                    json.dumps(
                        asdict(evaluation.before),
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        asdict(evaluation.after),
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        [
                            asdict(item)
                            for item in evaluation.metric_changes
                        ],
                        ensure_ascii=False,
                    ),
                    evaluation.notes,
                    json.dumps(
                        evaluation.run_snapshot,
                        ensure_ascii=False,
                        default=str,
                    ),
                    evaluation.evaluated_at,
                ),
            )
            connection.commit()

    def exists_for_run(
        self,
        run_id: str,
    ) -> bool:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM outcome_evaluations
                WHERE run_id = ?
                LIMIT 1
                """,
                (run_id,),
            ).fetchone()
        return row is not None

    def list_evaluations(
        self,
        limit: int = 500,
    ) -> list[OutcomeEvaluation]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM outcome_evaluations
                ORDER BY evaluated_at DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()

        return [
            self._row_to_evaluation(row)
            for row in rows
        ]

    def latest(
        self,
    ) -> OutcomeEvaluation | None:
        items = self.list_evaluations(limit=1)
        return items[0] if items else None

    def delete(
        self,
        evaluation_id: str,
    ) -> bool:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                DELETE FROM outcome_evaluations
                WHERE evaluation_id = ?
                """,
                (evaluation_id,),
            )
            connection.commit()
        return bool(cursor.rowcount)

    def clear(self) -> int:
        with closing(self._connect()) as connection:
            count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM outcome_evaluations"
                ).fetchone()[0]
            )
            connection.execute(
                "DELETE FROM outcome_evaluations"
            )
            connection.commit()
        return count

    def summary(self) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            total, successes, failures, neutral, average = (
                connection.execute(
                    """
                    SELECT
                        COUNT(*),
                        SUM(CASE WHEN classification='SUCCESS' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN classification='FAILURE' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN classification='NEUTRAL' THEN 1 ELSE 0 END),
                        COALESCE(AVG(reward), 0)
                    FROM outcome_evaluations
                    """
                ).fetchone()
            )

            best_agent = connection.execute(
                """
                SELECT
                    winning_agent,
                    COUNT(*) AS decisions,
                    AVG(reward) AS average_reward,
                    SUM(CASE WHEN classification='SUCCESS' THEN 1 ELSE 0 END)
                        * 1.0 / COUNT(*) AS success_rate
                FROM outcome_evaluations
                GROUP BY winning_agent
                ORDER BY average_reward DESC, decisions DESC
                LIMIT 1
                """
            ).fetchone()

        return {
            "total": int(total or 0),
            "successes": int(successes or 0),
            "failures": int(failures or 0),
            "neutral": int(neutral or 0),
            "average_reward": float(average or 0.0),
            "best_agent": (
                str(best_agent[0])
                if (
                    best_agent
                    and int(best_agent[1]) >= 3
                    and abs(float(best_agent[2])) >= 0.05
                )
                else "Insufficient evidence"
            ),
            "best_agent_average_reward": (
                float(best_agent[2])
                if (
                    best_agent
                    and int(best_agent[1]) >= 3
                    and abs(float(best_agent[2])) >= 0.05
                )
                else 0.0
            ),
            "best_agent_success_rate": (
                float(best_agent[3])
                if (
                    best_agent
                    and int(best_agent[1]) >= 3
                    and abs(float(best_agent[2])) >= 0.05
                )
                else 0.0
            ),
        }

    def agent_statistics(
        self,
    ) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT
                    winning_agent,
                    COUNT(*) AS decision_count,
                    AVG(reward) AS average_reward,
                    MIN(reward) AS minimum_reward,
                    MAX(reward) AS maximum_reward,
                    SUM(CASE WHEN classification='SUCCESS' THEN 1 ELSE 0 END)
                        * 1.0 / COUNT(*) AS success_rate,
                    SUM(CASE WHEN classification='FAILURE' THEN 1 ELSE 0 END)
                        * 1.0 / COUNT(*) AS failure_rate
                FROM outcome_evaluations
                GROUP BY winning_agent
                ORDER BY average_reward DESC
                """
            ).fetchall()

        return [
            {
                "agent": str(row[0]),
                "decision_count": int(row[1]),
                "average_reward": float(row[2]),
                "minimum_reward": float(row[3]),
                "maximum_reward": float(row[4]),
                "success_rate": float(row[5]),
                "failure_rate": float(row[6]),
                "reliability": self._reliability(
                    float(row[2]),
                    float(row[5]),
                    int(row[1]),
                ),
            }
            for row in rows
        ]

    def operation_statistics(
        self,
    ) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT
                    primary_operation,
                    COUNT(*) AS decision_count,
                    AVG(reward) AS average_reward,
                    SUM(CASE WHEN classification='SUCCESS' THEN 1 ELSE 0 END)
                        * 1.0 / COUNT(*) AS success_rate
                FROM outcome_evaluations
                GROUP BY primary_operation
                ORDER BY average_reward DESC
                """
            ).fetchall()

        return [
            {
                "operation": str(row[0]),
                "decision_count": int(row[1]),
                "average_reward": float(row[2]),
                "success_rate": float(row[3]),
            }
            for row in rows
        ]

    @staticmethod
    def _reliability(
        average_reward: float,
        success_rate: float,
        decisions: int,
    ) -> float:
        reward_score = (average_reward + 1.0) / 2.0
        evidence_factor = min(1.0, decisions / 20.0)
        raw = (
            0.55 * reward_score
            + 0.35 * success_rate
            + 0.10 * evidence_factor
        )
        return max(0.0, min(1.0, raw))

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.database_path)
        )
        connection.row_factory = sqlite3.Row
        return connection

    def _row_to_evaluation(
        self,
        row: sqlite3.Row,
    ) -> OutcomeEvaluation:
        before = OutcomeMetrics(
            **json.loads(row["before_json"])
        )
        after = OutcomeMetrics(
            **json.loads(row["after_json"])
        )
        changes = tuple(
            MetricChange(**item)
            for item in json.loads(
                row["changes_json"]
            )
        )

        return OutcomeEvaluation(
            evaluation_id=str(row["evaluation_id"]),
            run_id=str(row["run_id"]),
            experiment_id=(
                str(row["experiment_id"])
                if row["experiment_id"]
                else None
            ),
            product_id=str(row["product_id"]),
            winning_agent=str(row["winning_agent"]),
            decision_type=str(row["decision_type"]),
            primary_operation=str(row["primary_operation"]),
            primary_value=float(row["primary_value"]),
            primary_unit=str(row["primary_unit"]),
            reward=float(row["reward"]),
            classification=str(row["classification"]),
            successful=bool(row["successful"]),
            before=before,
            after=after,
            metric_changes=changes,
            notes=str(row["notes"]),
            evaluated_at=str(row["evaluated_at"]),
            run_snapshot=json.loads(
                row["run_snapshot_json"]
            ),
        )
