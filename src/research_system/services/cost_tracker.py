"""Cost tracking and budget management."""

from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import json

from ..config.settings import settings


class CostTracker:
    """
    Track API usage costs and enforce budget limits.

    Provides real-time cost monitoring, budget alerts, and monthly reporting.
    """

    def __init__(self, budget_monthly: Optional[float] = None):
        """
        Initialize cost tracker.

        Args:
            budget_monthly: Monthly budget in USD (defaults to settings)
        """
        self.budget = budget_monthly or settings.monthly_budget
        self.alert_threshold = settings.cost_alert_threshold
        self.cost_file = settings.data_dir / "costs.json"
        self.costs = self._load_costs()

    def _load_costs(self) -> Dict[str, list]:
        """Load cost history from file."""
        if self.cost_file.exists():
            return json.loads(self.cost_file.read_text())
        return {}

    def _save_costs(self) -> None:
        """Save cost history to file."""
        self.cost_file.parent.mkdir(parents=True, exist_ok=True)
        self.cost_file.write_text(json.dumps(self.costs, indent=2))

    def track_api_call(
        self,
        agent: str,
        tokens_used: int,
        cost: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an API call with its cost.

        Args:
            agent: Name of agent making the call
            tokens_used: Total tokens (input + output)
            cost: Cost in USD
            metadata: Additional metadata
        """
        month_key = datetime.now().strftime("%Y-%m")

        if month_key not in self.costs:
            self.costs[month_key] = []

        self.costs[month_key].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "tokens": tokens_used,
            "cost": cost,
            "metadata": metadata or {}
        })

        self._save_costs()
        self._check_budget_alert()

    def get_month_cost(self, month: Optional[str] = None) -> float:
        """
        Get total cost for a specific month.

        Args:
            month: Month in YYYY-MM format (defaults to current month)

        Returns:
            Total cost in USD
        """
        if month is None:
            month = datetime.now().strftime("%Y-%m")

        if month not in self.costs:
            return 0.0

        return sum(entry["cost"] for entry in self.costs[month])

    def get_budget_status(self) -> Dict[str, Any]:
        """
        Get current budget status.

        Returns:
            Dictionary with budget information
        """
        current_month_cost = self.get_month_cost()
        remaining = self.budget - current_month_cost
        percent_used = (current_month_cost / self.budget) * 100 if self.budget > 0 else 0

        return {
            "budget": self.budget,
            "spent": current_month_cost,
            "remaining": remaining,
            "percent_used": percent_used,
            "alert_threshold_reached": percent_used >= (self.alert_threshold * 100)
        }

    def _check_budget_alert(self) -> None:
        """Check if budget alert threshold reached and warn user."""
        status = self.get_budget_status()

        if status["alert_threshold_reached"]:
            print(f"\n⚠️  BUDGET ALERT: {status['percent_used']:.1f}% of ${self.budget:.2f} used")
            print(f"   Spent: ${status['spent']:.2f} | Remaining: ${status['remaining']:.2f}\n")

    def estimate_cost(
        self,
        prompt_tokens: int,
        expected_output_tokens: int
    ) -> float:
        """
        Estimate cost before making API call.

        Args:
            prompt_tokens: Number of input tokens
            expected_output_tokens: Expected number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Claude Sonnet 4.5 pricing: $3/MTok input, $15/MTok output
        input_cost = (prompt_tokens / 1_000_000) * 3.0
        output_cost = (expected_output_tokens / 1_000_000) * 15.0
        return input_cost + output_cost

    def can_afford(self, estimated_cost: float) -> tuple[bool, str]:
        """
        Check if operation is within budget.

        Args:
            estimated_cost: Estimated cost in USD

        Returns:
            Tuple of (can_afford, reason)
        """
        status = self.get_budget_status()
        new_total = status["spent"] + estimated_cost

        if new_total > self.budget:
            return False, f"Would exceed budget: ${new_total:.2f} > ${self.budget:.2f}"

        return True, "Within budget"

    def get_monthly_report(self) -> Dict[str, Any]:
        """
        Generate monthly cost report.

        Returns:
            Dictionary with cost breakdown
        """
        month = datetime.now().strftime("%Y-%m")
        entries = self.costs.get(month, [])

        # Group by agent
        by_agent = {}
        for entry in entries:
            agent = entry["agent"]
            if agent not in by_agent:
                by_agent[agent] = {"calls": 0, "tokens": 0, "cost": 0.0}

            by_agent[agent]["calls"] += 1
            by_agent[agent]["tokens"] += entry["tokens"]
            by_agent[agent]["cost"] += entry["cost"]

        return {
            "month": month,
            "total_cost": self.get_month_cost(),
            "total_calls": len(entries),
            "total_tokens": sum(e["tokens"] for e in entries),
            "by_agent": by_agent,
            "budget_status": self.get_budget_status()
        }

    def print_monthly_report(self) -> None:
        """Print formatted monthly cost report."""
        report = self.get_monthly_report()

        print(f"\n{'='*60}")
        print(f"COST REPORT - {report['month']}")
        print(f"{'='*60}")
        print(f"Total Cost: ${report['total_cost']:.2f} / ${self.budget:.2f}")
        print(f"Total Calls: {report['total_calls']}")
        print(f"Total Tokens: {report['total_tokens']:,}")
        print(f"\nBy Agent:")

        for agent, stats in report["by_agent"].items():
            print(f"  {agent}:")
            print(f"    Calls: {stats['calls']}")
            print(f"    Tokens: {stats['tokens']:,}")
            print(f"    Cost: ${stats['cost']:.2f}")

        status = report["budget_status"]
        print(f"\nBudget Status: {status['percent_used']:.1f}% used")
        print(f"Remaining: ${status['remaining']:.2f}")
        print(f"{'='*60}\n")


# Global cost tracker instance
cost_tracker = CostTracker()
