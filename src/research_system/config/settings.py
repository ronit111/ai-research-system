"""Configuration management using Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Keys
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude")

    # Paths (project now in Obsidian vault - auto-backed up to OneDrive)
    project_root: Path = Field(
        default=Path.home() / "Library/CloudStorage/OneDrive-Personal/Obsidian-Vault/Second Brain/ai-research-system",
        description="Project root directory"
    )
    obsidian_vault_path: Path = Field(
        default=Path.home() / "Library/CloudStorage/OneDrive-Personal/Obsidian-Vault/Second Brain/AI-Research",
        description="Path to Obsidian vault for research notes"
    )

    @property
    def data_dir(self) -> Path:
        """Data directory within project root."""
        return self.project_root / "data"

    # Knowledge Graph
    kg_context: str = Field(default="ai-research", description="Knowledge graph database context")

    # Budget Settings
    monthly_budget: float = Field(default=50.0, description="Monthly budget in USD")
    cost_alert_threshold: float = Field(default=0.8, description="Alert when this % of budget used")

    # Research Settings
    default_max_papers: int = Field(default=5, description="Default number of papers to retrieve")
    default_domain: str = Field(default="machine_learning", description="Default research domain")

    # Model Settings
    model_name: str = Field(default="claude-sonnet-4-5-20250929", description="Claude model to use")
    max_tokens: int = Field(default=4000, description="Maximum tokens per LLM call")

    @property
    def projects_dir(self) -> Path:
        """Directory for research projects."""
        return self.data_dir / "projects"

    @property
    def cache_dir(self) -> Path:
        """Directory for API response cache."""
        return self.data_dir / "cache"

    @property
    def database_path(self) -> Path:
        """Path to SQLite database."""
        return self.data_dir / "research.db"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.obsidian_vault_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_directories()
