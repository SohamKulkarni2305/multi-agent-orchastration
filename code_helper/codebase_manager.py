"""
codebase_manager.py — Dynamic Codebase Ingestion & Workspace State Management.
Enables users to upload .zip archives or Python source files, inspect architecture,
and query the active codebase.
"""

import ast
import io
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

from .tools.diagram_tool import generate_architecture_diagram

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "build",
    "dist",
    "docs",
    "skills",
    ".adk",
}

UPLOADS_BASE = Path(__file__).resolve().parent.parent / "uploads"
DEFAULT_WORKSPACE = Path(__file__).resolve().parent.parent


class CodebaseManager:
    """Manages active codebase target directory, uploads, extraction, and AST scanning."""

    def __init__(self) -> None:
        self.active_dir: Path = DEFAULT_WORKSPACE
        self.active_name: str = "Workspace (Default)"
        self.is_uploaded: bool = False
        UPLOADS_BASE.mkdir(parents=True, exist_ok=True)

    def get_active_dir(self) -> Path:
        """Return canonical path to current active codebase directory."""
        if not self.active_dir.exists():
            self.active_dir = DEFAULT_WORKSPACE
            self.active_name = "Workspace (Default)"
            self.is_uploaded = False
        return self.active_dir

    def scan_files(self, target: Path | None = None) -> list[Path]:
        """Scan target directory recursively for valid Python source files."""
        root = target or self.get_active_dir()
        if not root.exists():
            return []

        files: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith(".")]
            for fn in filenames:
                if fn.endswith(".py"):
                    p = Path(dirpath) / fn
                    parts = set(p.parts)
                    if "uploads" in parts and p.is_relative_to(UPLOADS_BASE) and root != p.parent and not p.is_relative_to(root):
                        continue
                    files.append(p)
        return sorted(files)

    def get_codebase_info(self) -> dict[str, Any]:
        """Gather metadata for active codebase: files count, lines of code, and structure."""
        active = self.get_active_dir()
        py_files = self.scan_files(active)

        total_loc = 0
        file_list: list[dict[str, Any]] = []

        for p in py_files:
            try:
                rel = str(p.relative_to(active)).replace("\\", "/")
            except ValueError:
                rel = p.name

            loc = 0
            classes = 0
            functions = 0
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                loc = len(lines)
                total_loc += loc

                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes += 1
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        functions += 1
            except Exception:
                pass

            file_list.append({
                "path": rel,
                "name": p.name,
                "loc": loc,
                "classes": classes,
                "functions": functions,
            })

        return {
            "name": self.active_name,
            "path": str(active),
            "is_uploaded": self.is_uploaded,
            "files_count": len(file_list),
            "total_loc": total_loc,
            "files": file_list,
        }

    def ingest_zip(self, zip_bytes: bytes, filename: str) -> dict[str, Any]:
        """
        Safely extract an uploaded .zip archive into uploads/current_codebase/
        and set as the active codebase.
        """
        clean_name = Path(filename).stem
        target_dir = UPLOADS_BASE / "current_codebase"

        # Wipe previous upload to keep disk clean
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        target_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for member in zf.infolist():
                # Protect against Zip Slip directory traversal
                member_path = Path(member.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    continue
                # Skip macOS metadata and git folders
                if any(p.startswith("__MACOSX") or p == ".git" for p in member_path.parts):
                    continue
                zf.extract(member, target_dir)

        # Detect if zip extracted into a single top-level folder
        children = [c for c in target_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        all_children = [c for c in target_dir.iterdir() if not c.name.startswith(".")]
        if len(children) == 1 and len(all_children) == 1:
            effective_root = children[0]
        else:
            effective_root = target_dir

        self.active_dir = effective_root
        self.active_name = clean_name
        self.is_uploaded = True

        info = self.get_codebase_info()
        diag = generate_architecture_diagram(str(effective_root))
        clean_mermaid = diag
        if "```mermaid" in diag:
            clean_mermaid = diag.split("```mermaid")[1].split("```")[0].strip()

        info["mermaid"] = clean_mermaid
        info["raw_diagram"] = diag
        return info

    def ingest_files(self, file_dict: dict[str, str]) -> dict[str, Any]:
        """
        Save individual uploaded Python files into uploads/current_codebase/
        and set as the active codebase.
        """
        target_dir = UPLOADS_BASE / "current_codebase"
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        target_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in file_dict.items():
            dest = target_dir / Path(filename).name
            dest.write_text(content, encoding="utf-8", errors="replace")

        self.active_dir = target_dir
        self.active_name = "Uploaded Files"
        self.is_uploaded = True

        info = self.get_codebase_info()
        diag = generate_architecture_diagram(str(target_dir))
        clean_mermaid = diag
        if "```mermaid" in diag:
            clean_mermaid = diag.split("```mermaid")[1].split("```")[0].strip()

        info["mermaid"] = clean_mermaid
        info["raw_diagram"] = diag
        return info

    def reset_to_default(self) -> dict[str, Any]:
        """Reset target back to the default project repository."""
        self.active_dir = DEFAULT_WORKSPACE
        self.active_name = "Workspace (Default)"
        self.is_uploaded = False
        info = self.get_codebase_info()
        diag = generate_architecture_diagram(str(DEFAULT_WORKSPACE))
        clean_mermaid = diag
        if "```mermaid" in diag:
            clean_mermaid = diag.split("```mermaid")[1].split("```")[0].strip()
        info["mermaid"] = clean_mermaid
        info["raw_diagram"] = diag
        return info


# Global Singleton instance
codebase_manager = CodebaseManager()
