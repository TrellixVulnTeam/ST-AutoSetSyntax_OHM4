from ..constraint import AbstractConstraint
from ..constraint import AlwaysFalsyException
from typing import final
import sublime


@final
class IsInGitRepoConstraint(AbstractConstraint):
    """Check whether this file is in a git repo."""

    def test(self, view: sublime.View) -> bool:
        view_info = self.get_view_info(view)

        # early return so that we may save some IO operations
        if not view_info["file_name"]:
            raise AlwaysFalsyException("file not on disk")

        # `.git/` directory for normal Git repo and `.git` file for Git worktree
        return self.has_sibling(view_info["file_path"], ".git", use_exists=True)