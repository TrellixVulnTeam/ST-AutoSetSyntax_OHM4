from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import sublime

from .constant import VIEW_RUN_ID_SETTINGS_KEY
from .helper import head_tail_content_st, remove_prefix
from .settings import get_merged_plugin_setting


@dataclass
class ViewSnapshot:
    id: int
    """View ID."""
    char_count: int
    """Character count."""
    content: str
    """Pseudo file content."""
    file_name: str
    """The file name. Empty string if not on a disk."""
    file_name_unhidden: str
    """The file name without prefixed dots. Empty string if not on a disk."""
    file_path: str
    """The full file path with `/` as the directory separator. Empty string if not on a disk."""
    file_size: int
    """In bytes, -1 if file not on a disk."""
    first_line: str
    """Pseudo first line."""
    line_count: int
    """Number of lines in the original content."""
    syntax: Optional[sublime.Syntax]
    """The syntax object. Note that the value is as-is when it's cached."""


class ViewSnapshotCollection:
    _snapshots: Dict[str, ViewSnapshot] = {}

    @classmethod
    def add(cls, cache_id: str, view: sublime.View) -> None:
        window = view.window() or sublime.active_window()

        # is real file on a disk?
        if (_path := view.file_name()) and (path := Path(_path).resolve()).is_file():
            file_name = path.name
            file_path = path.as_posix()
            file_size = path.stat().st_size
        else:
            file_name = ""
            file_path = ""
            file_size = -1

        cls.set(
            cache_id,
            ViewSnapshot(
                id=view.id(),
                char_count=view.size(),
                content=get_view_pseudo_content(view, window),
                file_name=file_name,
                file_name_unhidden=remove_prefix(file_name, "."),
                file_path=file_path,
                file_size=file_size,
                first_line=get_view_pseudo_first_line(view, window),
                line_count=view.rowcol(view.size())[0] + 1,
                syntax=view.syntax(),
            ),
        )

    @classmethod
    def get(cls, cache_id: str) -> Optional[ViewSnapshot]:
        return cls._snapshots.get(cache_id, None)

    @classmethod
    def get_by_view(cls, view: sublime.View) -> Optional[ViewSnapshot]:
        return cls.get(view.settings().get(VIEW_RUN_ID_SETTINGS_KEY))

    @classmethod
    def set(cls, cache_id: str, snapshot: ViewSnapshot) -> None:
        cls._snapshots[cache_id] = snapshot

    @classmethod
    def pop(cls, cache_id: str) -> Optional[ViewSnapshot]:
        return cls._snapshots.pop(cache_id, None)


def get_view_pseudo_content(view: sublime.View, window: sublime.Window) -> str:
    return head_tail_content_st(view, get_merged_plugin_setting("trim_file_size", window=window))


def get_view_pseudo_first_line(view: sublime.View, window: sublime.Window) -> str:
    region = view.line(0)
    if (max_length := get_merged_plugin_setting("trim_first_line_length", window=window)) >= 0:
        region = sublime.Region(region.a, min(region.b, max_length))
    return view.substr(region)
