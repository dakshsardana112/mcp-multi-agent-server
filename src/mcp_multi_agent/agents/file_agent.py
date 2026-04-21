"""File organizer agent.

Scans a directory and groups files by extension category
(documents / images / code / archives / other). No side effects - this
agent never moves or deletes anything; it only *reports*. If you later
want real organization (moving files into sorted folders), wrap the
``file_move`` pattern in a separate tool with a dry-run flag.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .base import BaseAgent

CATEGORIES: dict[str, tuple[str, ...]] = {
    "documents": (".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt"),
    "spreadsheets": (".xls", ".xlsx", ".csv", ".tsv", ".ods"),
    "presentations": (".ppt", ".pptx", ".odp"),
    "images": (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp", ".heic"),
    "audio": (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"),
    "video": (".mp4", ".mov", ".avi", ".mkv", ".webm"),
    "archives": (".zip", ".tar", ".gz", ".7z", ".rar", ".bz2"),
    "code": (
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".c", ".cpp",
        ".h", ".hpp", ".java", ".rb", ".php", ".sh", ".html", ".css",
    ),
}


def _category_for(ext: str) -> str:
    ext = ext.lower()
    for cat, exts in CATEGORIES.items():
        if ext in exts:
            return cat
    return "other"


def _safe_path(raw: str) -> Path:
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = p.resolve()
    return p


class FileAgent(BaseAgent):
    name = "file"

    def register(self, mcp: FastMCP) -> None:

        @mcp.tool()
        def file_scan(path: str, recursive: bool = False) -> dict[str, Any]:
            """List files under ``path``. Returns per-file info + category.

            Args:
                path: Directory to scan.
                recursive: If True, walk subdirectories too.
            """
            p = _safe_path(path)
            if not p.exists():
                raise FileNotFoundError(f"path does not exist: {p}")
            if not p.is_dir():
                raise NotADirectoryError(f"path is not a directory: {p}")
            results: list[dict[str, Any]] = []
            if recursive:
                walker = (Path(r) / f for r, _, fs in os.walk(p) for f in fs)
            else:
                walker = (x for x in p.iterdir() if x.is_file())
            for f in walker:
                try:
                    stat = f.stat()
                except OSError:
                    continue
                results.append(
                    {
                        "name": f.name,
                        "path": str(f),
                        "size_bytes": stat.st_size,
                        "extension": f.suffix.lower(),
                        "category": _category_for(f.suffix),
                    }
                )
            return {
                "path": str(p),
                "recursive": recursive,
                "count": len(results),
                "files": results,
            }

        @mcp.tool()
        def file_summary(path: str, recursive: bool = False) -> dict[str, Any]:
            """Aggregate: count + total bytes per category."""
            scan = file_scan(path, recursive=recursive)  # reuse!
            summary: dict[str, dict[str, int]] = {}
            for f in scan["files"]:
                cat = f["category"]
                s = summary.setdefault(cat, {"count": 0, "size_bytes": 0})
                s["count"] += 1
                s["size_bytes"] += f["size_bytes"]
            return {
                "path": scan["path"],
                "recursive": recursive,
                "total_files": scan["count"],
                "by_category": summary,
            }

        @mcp.tool()
        def file_search(
            path: str,
            name_contains: str,
            recursive: bool = True,
            category: Optional[str] = None,
        ) -> list[dict[str, Any]]:
            """Search for files whose name contains a substring (case-insensitive)."""
            if not name_contains.strip():
                raise ValueError("name_contains cannot be empty")
            if category is not None and category not in list(CATEGORIES.keys()) + ["other"]:
                raise ValueError(
                    f"category must be one of {list(CATEGORIES.keys()) + ['other']}"
                )
            scan = file_scan(path, recursive=recursive)
            needle = name_contains.lower()
            hits = [
                f for f in scan["files"]
                if needle in f["name"].lower()
                and (category is None or f["category"] == category)
            ]
            return hits

        @mcp.tool()
        def file_categories() -> dict[str, list[str]]:
            """Show which extensions map to which category. Pure-info tool."""
            return {k: list(v) for k, v in CATEGORIES.items()}
