"""Runtime bootstrap for repository-backed workflows and tool wiring."""

from functools import lru_cache

from backend.database.repositories import build_repository
from backend.tools import evidence_tools, ledger_tools, opportunity_tools, policy_tools, submission_tools, vault_tools


def _wire_tool_repositories(repository) -> None:
    evidence_tools.configure_repository(repository)
    ledger_tools.configure_repository(repository)
    opportunity_tools.configure_repository(repository)
    policy_tools.configure_repository(repository)
    submission_tools.configure_repository(repository)
    vault_tools.configure_repository(repository)


@lru_cache(maxsize=1)
def get_repository():
    repository = build_repository()
    _wire_tool_repositories(repository)
    return repository