from .constant import VIEW_RUN_ID_SETTINGS_KEY
from .helper import head_tail_content_st
from .settings import get_merged_plugin_setting
from .types import TD_ViewSnapshot
from pathlib import Path
from typing import Dict, Optional
import sublime


class ViewSnapshot:
    snapshots: Dict[str, TD_ViewSnapshot] = {}

    @classmethod
    def add(cls, cache_id: str, view: sublime.View) -> None:
        window = view.window() or sublime.active_window()

        # is real file on a disk?
        if (filepath := view.file_name()) and (p := Path(filepath)).is_file():
            filename = p.name
            filepath = p.as_posix()  # always use "/" as the path separator
            filesize = p.stat().st_size
        else:
            filename = ""
            filepath = ""
            filesize = -1

        cls.snapshots[cache_id] = {
            "id": view.id(),
            "char_count": view.size(),
            "content": get_view_pseudo_content(view, window),
            "file_name": filename,
            "file_path": filepath,
            "file_size": filesize,
            "first_line": get_view_pseudo_first_line(view, window),
            "syntax": view.syntax(),
        }

    @classmethod
    def get_by_view(cls, view: sublime.View) -> Optional[TD_ViewSnapshot]:
        return cls.get(view.settings().get(VIEW_RUN_ID_SETTINGS_KEY))

    @classmethod
    def get(cls, cache_id: str) -> Optional[TD_ViewSnapshot]:
        return cls.snapshots.get(cache_id, None)

    @classmethod
    def remove(cls, cache_id: str) -> Optional[TD_ViewSnapshot]:
        return cls.snapshots.pop(cache_id, None)


def get_view_pseudo_content(view: sublime.View, window: sublime.Window) -> str:
    return head_tail_content_st(view, get_merged_plugin_setting(window, "trim_file_size"))


def get_view_pseudo_first_line(view: sublime.View, window: sublime.Window) -> str:
    if (max_length := get_merged_plugin_setting(window, "trim_first_line_length")) >= 0:
        return view.substr(sublime.Region(0, max_length)).partition("\n")[0]
    return view.substr(view.line(0))
