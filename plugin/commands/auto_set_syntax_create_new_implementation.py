from ..constant import PLUGIN_CUSTOM_DIR
from ..constant import PLUGIN_CUSTOM_MODULE_PATHS
from ..constant import PLUGIN_NAME
from ..helper import find_syntax_by_syntax_like
from abc import ABCMeta
from pathlib import Path
from typing import Optional, Union
import sublime
import sublime_plugin


class AbstractCreateNewImplementationCommand(sublime_plugin.TextCommand, metaclass=ABCMeta):
    template_type = ""
    template_file = ""
    template_syntax: Optional[str] = None
    save_dir = ""

    def description(self) -> str:
        return f"{PLUGIN_NAME}: Create New {self.template_type}"

    def run(self, edit: sublime.Edit) -> None:
        if not (new := _clone_file_as_template(self.view, edit, self.template_file, self.template_syntax)):
            return

        save_dir = Path(self.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        with (Path(PLUGIN_CUSTOM_DIR) / ".python-version").open("w", encoding="utf-8") as f:
            f.write("3.8\n")

        new.settings().update(
            {
                "default_dir": str(save_dir),
                "is_auto_set_syntax_template_buffer": True,
            }
        )


class AutoSetSyntaxCreateNewConstraintCommand(AbstractCreateNewImplementationCommand):
    template_type = "Constraint"
    template_file = f"Packages/{PLUGIN_NAME}/templates/example_constraint.py"
    template_syntax = "scope:source.python"
    save_dir = str(PLUGIN_CUSTOM_MODULE_PATHS["constraint"])


class AutoSetSyntaxCreateNewMatchCommand(AbstractCreateNewImplementationCommand):
    template_type = "Match"
    template_file = f"Packages/{PLUGIN_NAME}/templates/example_match.py"
    template_syntax = "scope:source.python"
    save_dir = str(PLUGIN_CUSTOM_MODULE_PATHS["match"])


def _clone_file_as_template(
    view: sublime.View,
    edit: sublime.Edit,
    source_path: str,
    syntax: Optional[Union[str, sublime.Syntax]] = None,
) -> Optional[sublime.View]:
    if not (window := view.window()):
        return None

    try:
        template = sublime.load_resource(source_path)
    except FileNotFoundError as e:
        sublime.error_message(str(e))
        return None

    new = window.new_file()
    new.insert(edit, 0, template)
    new.show(0)

    if syntax and (syntax := find_syntax_by_syntax_like(syntax)):
        new.assign_syntax(syntax)

    sel = new.sel()
    sel.clear()
    sel.add(0)

    return new