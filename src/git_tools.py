"""GitHub tools for SAM agents."""
import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

async def github_get_commits(repo: str, count: int = 10, since: Optional[str] = None, branch: Optional[str] = None, tool_context: Optional[Any] = None, tool_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get recent commits from a GitHub repository."""
    try:
        from github import Github
        token = tool_config.get("github_token") if tool_config else None
        g = Github(token) if token else Github()
        repository = g.get_repo(repo)
        commits = []
        for i, c in enumerate(repository.get_commits()):
            if i >= count: break
            commits.append({"sha": c.sha[:7], "message": c.commit.message.split("\n")[0], "author": c.commit.author.name if c.commit.author else "unknown", "date": c.commit.author.date.strftime("%Y-%m-%d") if c.commit.author else ""})
        return {"status": "success", "repository": repo, "commits": commits}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def github_get_releases(repo: str, count: int = 10, include_prereleases: bool = False, tool_context: Optional[Any] = None, tool_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get releases from a GitHub repository."""
    try:
        from github import Github
        token = tool_config.get("github_token") if tool_config else None
        g = Github(token) if token else Github()
        releases = []
        for i, r in enumerate(g.get_repo(repo).get_releases()):
            if i >= count: break
            if not include_prereleases and r.prerelease: continue
            releases.append({"tag": r.tag_name, "name": r.title, "date": r.published_at.strftime("%Y-%m-%d") if r.published_at else "", "body": r.body[:500] if r.body else ""})
        return {"status": "success", "repository": repo, "releases": releases}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def github_compare_commits(repo: str, base: str, head: str, tool_context: Optional[Any] = None, tool_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Compare two commits, branches, or tags."""
    try:
        from github import Github
        token = tool_config.get("github_token") if tool_config else None
        g = Github(token) if token else Github()
        comp = g.get_repo(repo).compare(base, head)
        commits = [{"sha": c.sha[:7], "message": c.commit.message.split("\n")[0]} for c in comp.commits[:50]]
        return {"status": "success", "repository": repo, "base": base, "head": head, "total_commits": comp.total_commits, "commits": commits}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def github_get_repo_info(repo: str, tool_context: Optional[Any] = None, tool_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get information about a GitHub repository."""
    try:
        from github import Github
        token = tool_config.get("github_token") if tool_config else None
        g = Github(token) if token else Github()
        r = g.get_repo(repo)
        return {"status": "success", "name": r.name, "description": r.description, "stars": r.stargazers_count, "language": r.language, "url": r.html_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}
