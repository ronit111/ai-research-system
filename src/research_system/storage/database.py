"""SQLite database wrapper for research project management."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import sqlite3
import json

from ..config.settings import settings


class Database:
    """
    SQLite database wrapper for storing research metadata.

    Handles projects, papers, experiments, and agent runs.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database (defaults to settings)
        """
        self.db_path = db_path or settings.database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                domain TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Papers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                arxiv_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                abstract TEXT,
                published_date TEXT,
                pdf_url TEXT,
                relevance_score REAL,
                project_id TEXT,
                added_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Agent runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT DEFAULT 'running',
                tokens_used INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                results TEXT,
                error TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Hypotheses table (Agent 3 output)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hypotheses (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                idea_title TEXT NOT NULL,
                hypothesis_text TEXT NOT NULL,
                null_hypothesis TEXT,
                independent_variables TEXT,
                dependent_variables TEXT,
                control_variables TEXT,
                success_criteria TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Experiment designs table (Agent 4 output)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_designs (
                id TEXT PRIMARY KEY,
                hypothesis_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                methodology TEXT NOT NULL,
                data_requirements TEXT,
                code_template TEXT,
                resource_estimates TEXT,
                platform TEXT DEFAULT 'local',
                status TEXT DEFAULT 'draft',
                created_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Experiment runs table (Agent 5 output)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_runs (
                id TEXT PRIMARY KEY,
                design_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                status TEXT DEFAULT 'queued',
                platform TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                duration_seconds REAL,
                compute_cost_usd REAL DEFAULT 0.0,
                results_data TEXT,
                logs TEXT,
                error TEXT,
                metadata TEXT,
                FOREIGN KEY (design_id) REFERENCES experiment_designs(id),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Analyses table (Agent 6 output)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                hypothesis_id TEXT NOT NULL,
                decision TEXT,
                p_value REAL,
                effect_size REAL,
                confidence_interval TEXT,
                insights TEXT,
                visualizations TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (run_id) REFERENCES experiment_runs(id),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hypotheses_project
            ON hypotheses(project_id, status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiment_designs_hypothesis
            ON experiment_designs(hypothesis_id, status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiment_runs_design
            ON experiment_runs(design_id, status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analyses_run
            ON analyses(run_id, hypothesis_id)
        """)

        self.conn.commit()

    def create_project(
        self,
        project_id: str,
        name: str,
        domain: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new research project.

        Args:
            project_id: Unique project identifier
            name: Project name
            domain: Research domain
            metadata: Additional metadata

        Returns:
            Created project data
        """
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO projects (id, name, domain, status, created_at, updated_at, metadata)
            VALUES (?, ?, ?, 'active', ?, ?, ?)
        """, (project_id, name, domain, now, now, json.dumps(metadata or {})))

        self.conn.commit()

        return {
            "id": project_id,
            "name": name,
            "domain": domain,
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {}
        }

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()

        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "domain": row["domain"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }

        return None

    def list_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all projects.

        Args:
            status: Filter by status (active, archived)

        Returns:
            List of projects
        """
        cursor = self.conn.cursor()

        if status:
            cursor.execute("SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")

        rows = cursor.fetchall()

        return [{
            "id": row["id"],
            "name": row["name"],
            "domain": row["domain"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
        } for row in rows]

    def add_paper(
        self,
        arxiv_id: str,
        title: str,
        authors: List[str],
        abstract: str,
        project_id: str,
        relevance_score: float = 0.0,
        published_date: Optional[str] = None,
        pdf_url: Optional[str] = None
    ) -> None:
        """
        Add a paper to the database.

        Args:
            arxiv_id: arXiv ID
            title: Paper title
            authors: List of authors
            abstract: Paper abstract
            project_id: Associated project ID
            relevance_score: Relevance score (0-10)
            published_date: Publication date
            pdf_url: PDF URL
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO papers
            (arxiv_id, title, authors, abstract, published_date, pdf_url,
             relevance_score, project_id, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            arxiv_id,
            title,
            json.dumps(authors),
            abstract,
            published_date,
            pdf_url,
            relevance_score,
            project_id,
            datetime.now().isoformat()
        ))

        self.conn.commit()

    def get_papers(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all papers for a project.

        Args:
            project_id: Project ID

        Returns:
            List of papers
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM papers WHERE project_id = ? ORDER BY relevance_score DESC
        """, (project_id,))

        rows = cursor.fetchall()

        return [{
            "arxiv_id": row["arxiv_id"],
            "title": row["title"],
            "authors": json.loads(row["authors"]),
            "abstract": row["abstract"],
            "published_date": row["published_date"],
            "pdf_url": row["pdf_url"],
            "relevance_score": row["relevance_score"],
            "added_at": row["added_at"]
        } for row in rows]

    def log_agent_run(
        self,
        project_id: str,
        agent_name: str,
        tokens_used: int,
        cost_usd: float,
        results: Dict[str, Any],
        status: str = "completed",
        error: Optional[str] = None
    ) -> int:
        """
        Log an agent execution.

        Args:
            project_id: Project ID
            agent_name: Name of agent
            tokens_used: Tokens consumed
            cost_usd: Cost in USD
            results: Agent results
            status: Run status
            error: Error message if failed

        Returns:
            Run ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO agent_runs
            (project_id, agent_name, started_at, completed_at, status,
             tokens_used, cost_usd, results, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            agent_name,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            status,
            tokens_used,
            cost_usd,
            json.dumps(results),
            error
        ))

        self.conn.commit()
        return cursor.lastrowid

    def add_hypothesis(
        self,
        hypothesis_id: str,
        project_id: str,
        idea_title: str,
        hypothesis_text: str,
        null_hypothesis: Optional[str] = None,
        independent_variables: Optional[List[str]] = None,
        dependent_variables: Optional[List[str]] = None,
        control_variables: Optional[List[str]] = None,
        success_criteria: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a hypothesis to the database."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO hypotheses
            (id, project_id, idea_title, hypothesis_text, null_hypothesis,
             independent_variables, dependent_variables, control_variables,
             success_criteria, status, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (
            hypothesis_id,
            project_id,
            idea_title,
            hypothesis_text,
            null_hypothesis,
            json.dumps(independent_variables or []),
            json.dumps(dependent_variables or []),
            json.dumps(control_variables or []),
            json.dumps(success_criteria or {}),
            datetime.now().isoformat(),
            json.dumps(metadata or {})
        ))

        self.conn.commit()

    def get_hypotheses(self, project_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get hypotheses for a project."""
        cursor = self.conn.cursor()

        if status:
            cursor.execute("""
                SELECT * FROM hypotheses
                WHERE project_id = ? AND status = ?
                ORDER BY created_at DESC
            """, (project_id, status))
        else:
            cursor.execute("""
                SELECT * FROM hypotheses
                WHERE project_id = ?
                ORDER BY created_at DESC
            """, (project_id,))

        rows = cursor.fetchall()

        return [{
            "id": row["id"],
            "project_id": row["project_id"],
            "idea_title": row["idea_title"],
            "hypothesis_text": row["hypothesis_text"],
            "null_hypothesis": row["null_hypothesis"],
            "independent_variables": json.loads(row["independent_variables"]),
            "dependent_variables": json.loads(row["dependent_variables"]),
            "control_variables": json.loads(row["control_variables"]),
            "success_criteria": json.loads(row["success_criteria"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
        } for row in rows]

    def add_experiment_design(
        self,
        design_id: str,
        hypothesis_id: str,
        project_id: str,
        methodology: str,
        data_requirements: Optional[Dict[str, Any]] = None,
        code_template: Optional[str] = None,
        resource_estimates: Optional[Dict[str, Any]] = None,
        platform: str = "local",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an experiment design to the database."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO experiment_designs
            (id, hypothesis_id, project_id, methodology, data_requirements,
             code_template, resource_estimates, platform, status, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
        """, (
            design_id,
            hypothesis_id,
            project_id,
            methodology,
            json.dumps(data_requirements or {}),
            code_template,
            json.dumps(resource_estimates or {}),
            platform,
            datetime.now().isoformat(),
            json.dumps(metadata or {})
        ))

        self.conn.commit()

    def get_experiment_designs(
        self,
        hypothesis_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get experiment designs."""
        cursor = self.conn.cursor()

        if hypothesis_id:
            cursor.execute("""
                SELECT * FROM experiment_designs
                WHERE hypothesis_id = ?
                ORDER BY created_at DESC
            """, (hypothesis_id,))
        elif project_id:
            cursor.execute("""
                SELECT * FROM experiment_designs
                WHERE project_id = ?
                ORDER BY created_at DESC
            """, (project_id,))
        else:
            return []

        rows = cursor.fetchall()

        return [{
            "id": row["id"],
            "hypothesis_id": row["hypothesis_id"],
            "project_id": row["project_id"],
            "methodology": row["methodology"],
            "data_requirements": json.loads(row["data_requirements"]),
            "code_template": row["code_template"],
            "resource_estimates": json.loads(row["resource_estimates"]),
            "platform": row["platform"],
            "status": row["status"],
            "created_at": row["created_at"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
        } for row in rows]

    def add_experiment_run(
        self,
        run_id: str,
        design_id: str,
        project_id: str,
        platform: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an experiment run to the database."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO experiment_runs
            (id, design_id, project_id, status, platform, started_at, metadata)
            VALUES (?, ?, ?, 'queued', ?, ?, ?)
        """, (
            run_id,
            design_id,
            project_id,
            platform,
            datetime.now().isoformat(),
            json.dumps(metadata or {})
        ))

        self.conn.commit()

    def update_experiment_run(
        self,
        run_id: str,
        status: Optional[str] = None,
        results_data: Optional[Dict[str, Any]] = None,
        logs: Optional[str] = None,
        error: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        compute_cost_usd: Optional[float] = None
    ) -> None:
        """Update an experiment run."""
        cursor = self.conn.cursor()

        updates = []
        values = []

        if status:
            updates.append("status = ?")
            values.append(status)
            if status == "completed":
                updates.append("completed_at = ?")
                values.append(datetime.now().isoformat())

        if results_data is not None:
            updates.append("results_data = ?")
            values.append(json.dumps(results_data))

        if logs is not None:
            updates.append("logs = ?")
            values.append(logs)

        if error is not None:
            updates.append("error = ?")
            values.append(error)

        if duration_seconds is not None:
            updates.append("duration_seconds = ?")
            values.append(duration_seconds)

        if compute_cost_usd is not None:
            updates.append("compute_cost_usd = ?")
            values.append(compute_cost_usd)

        if updates:
            values.append(run_id)
            cursor.execute(f"""
                UPDATE experiment_runs
                SET {', '.join(updates)}
                WHERE id = ?
            """, values)

            self.conn.commit()

    def get_experiment_runs(
        self,
        design_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get experiment runs."""
        cursor = self.conn.cursor()

        if design_id:
            cursor.execute("""
                SELECT * FROM experiment_runs
                WHERE design_id = ?
                ORDER BY started_at DESC
            """, (design_id,))
        elif project_id:
            cursor.execute("""
                SELECT * FROM experiment_runs
                WHERE project_id = ?
                ORDER BY started_at DESC
            """, (project_id,))
        else:
            return []

        rows = cursor.fetchall()

        return [{
            "id": row["id"],
            "design_id": row["design_id"],
            "project_id": row["project_id"],
            "status": row["status"],
            "platform": row["platform"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "duration_seconds": row["duration_seconds"],
            "compute_cost_usd": row["compute_cost_usd"],
            "results_data": json.loads(row["results_data"]) if row["results_data"] else None,
            "logs": row["logs"],
            "error": row["error"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
        } for row in rows]

    def add_analysis(
        self,
        analysis_id: str,
        run_id: str,
        project_id: str,
        hypothesis_id: str,
        decision: str,
        p_value: Optional[float] = None,
        effect_size: Optional[float] = None,
        confidence_interval: Optional[Dict[str, Any]] = None,
        insights: Optional[str] = None,
        visualizations: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an analysis to the database."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO analyses
            (id, run_id, project_id, hypothesis_id, decision, p_value,
             effect_size, confidence_interval, insights, visualizations,
             status, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?)
        """, (
            analysis_id,
            run_id,
            project_id,
            hypothesis_id,
            decision,
            p_value,
            effect_size,
            json.dumps(confidence_interval or {}),
            insights,
            json.dumps(visualizations or []),
            datetime.now().isoformat(),
            json.dumps(metadata or {})
        ))

        self.conn.commit()

    def get_analyses(
        self,
        run_id: Optional[str] = None,
        hypothesis_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get analyses."""
        cursor = self.conn.cursor()

        if run_id:
            cursor.execute("""
                SELECT * FROM analyses
                WHERE run_id = ?
                ORDER BY created_at DESC
            """, (run_id,))
        elif hypothesis_id:
            cursor.execute("""
                SELECT * FROM analyses
                WHERE hypothesis_id = ?
                ORDER BY created_at DESC
            """, (hypothesis_id,))
        elif project_id:
            cursor.execute("""
                SELECT * FROM analyses
                WHERE project_id = ?
                ORDER BY created_at DESC
            """, (project_id,))
        else:
            return []

        rows = cursor.fetchall()

        return [{
            "id": row["id"],
            "run_id": row["run_id"],
            "project_id": row["project_id"],
            "hypothesis_id": row["hypothesis_id"],
            "decision": row["decision"],
            "p_value": row["p_value"],
            "effect_size": row["effect_size"],
            "confidence_interval": json.loads(row["confidence_interval"]),
            "insights": row["insights"],
            "visualizations": json.loads(row["visualizations"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
        } for row in rows]

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()


# Global database instance
db = Database()
