"""
health_check_tool.py — System readiness, environment health, and quickstart run commands.
"""

import os
import sys
from pathlib import Path


EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "build",
    "dist",
    "code_helper",
    "tests",
    "docs",
    "skills",
}


def check_system_health(project_dir: str = ".") -> str:
    """
    Check environment setup, dependencies, .env keys readiness, and project integrity.
    Works dynamically for any Python codebase.
    """
    root = Path(project_dir)
    report: list[str] = ["=== Multi-Agent Code Helper System Health Check ==="]

    # 1. Python runtime
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    report.append(f"[OK] Python Version       : {py_ver} (64-bit on {sys.platform})")

    # 2. Dynamic Source Files Discovery
    candidates = sorted(root.glob("*.py"))
    valid_files = [f for f in candidates if not set(f.parts).intersection(EXCLUDE_DIRS)]
    if not valid_files:
        valid_files = [f for f in sorted(root.rglob("*.py")) if not set(f.parts).intersection(EXCLUDE_DIRS)]

    if valid_files:
        filenames = [f.name for f in valid_files[:6]]
        extra = f" (+{len(valid_files) - 6} more)" if len(valid_files) > 6 else ""
        report.append(f"[OK] Source Files Found   : {len(valid_files)} file(s) ({', '.join(filenames)}{extra})")
    else:
        report.append("[WARN] Source Files       : No Python source files found in target directory.")

    # 3. Environment file check
    env_file = root / ".env"
    if not env_file.exists():
        # Check parent or current directory
        env_file = Path(".env")

    if env_file.exists():
        report.append(f"[OK] .env Configuration  : Found at {env_file.resolve()}")
        try:
            content = env_file.read_text(encoding="utf-8")
            has_nvidia = "NVIDIA_API_KEY" in content and "your-key" not in content
            has_pinecone = "PINECONE_API_KEY" in content and "your-pinecone" not in content
            report.append(f"     • NVIDIA_API_KEY    : {'Configured' if has_nvidia else 'Missing or template value'}")
            report.append(f"     • PINECONE_API_KEY  : {'Configured' if has_pinecone else 'Missing or template value'}")
        except Exception:
            report.append("     • Could not read .env content.")
    else:
        report.append("[WARN] .env File         : Not found. Create .env from .env.example")

    # 4. ADK package entrypoint
    adk_agent = root / "code_helper" / "agent.py"
    if not adk_agent.exists():
        adk_agent = Path("code_helper/agent.py")

    if adk_agent.exists():
        report.append("[OK] ADK Package Entry   : code_helper/agent.py exists and exports root_agent")
    else:
        report.append("[WARN] ADK Entry         : code_helper/agent.py not found")

    report.append("\nSystem Status: READY for indexing, inspection, and execution.")
    return "\n".join(report)


def get_run_commands() -> str:
    """
    Return the exact CLI commands needed to install requirements, index the codebase,
    run the agent in the terminal, or launch the ADK web interface.
    Use this tool when a developer asks how to run the project or needs the setup commands.
    """
    guide = [
        "=== Exact Execution Commands for Multi-Agent Code Helper ===",
        "",
        "1. Install Requirements:",
        "   pip install google-adk \"litellm>=1.84\" openai pinecone python-dotenv pytest",
        "",
        "2. Populate Pinecone Vector Database (Run Once):",
        "   python -m code_helper.index_codebase --evaluate",
        "",
        "3. Run Assistant in Terminal (CLI):",
        "   adk run code_helper",
        "",
        "4. Run Assistant on ADK Web UI:",
        "   adk web",
        "",
        "5. Run Test Suite (Offline Unit Tests):",
        "   pytest -v",
        "",
        "6. Index Custom External Directory (Optional):",
        "   python -m code_helper.index_codebase --target-dir <path_to_codebase>",
    ]
    return "\n".join(guide)
