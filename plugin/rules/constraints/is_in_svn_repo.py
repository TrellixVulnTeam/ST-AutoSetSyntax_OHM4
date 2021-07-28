from ..constraint import AbstractConstraint
import sublime


class IsInSvnRepoConstraint(AbstractConstraint):
    """Check whether this file is in a SVN repo."""

    def test(self, view: sublime.View) -> bool:
        view_info = self.get_view_info(view)

        # early return so that we may save some IO operations
        if not view_info["file_name"]:
            return False

        return self.has_sibling(view_info["file_path"], ".svn/")