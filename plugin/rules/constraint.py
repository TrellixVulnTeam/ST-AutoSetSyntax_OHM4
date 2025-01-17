from __future__ import annotations

import operator
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, Optional, Pattern, Tuple, Type, TypeVar, Union, final

import sublime

from ..constant import PLUGIN_NAME, ST_PLATFORM
from ..helper import (
    camel_to_snake,
    compile_regex,
    first,
    get_all_subclasses,
    merge_regexes,
    parse_regex_flags,
    remove_suffix,
)
from ..lru_cache import clearable_lru_cache
from ..snapshot import ViewSnapshot, ViewSnapshotCollection
from ..types import Optimizable, ST_ConstraintRule

T = TypeVar("T")


def find_constraint(obj: Any) -> Optional[Type[AbstractConstraint]]:
    return first(get_constraints(), lambda t: t.is_supported(obj))


@clearable_lru_cache()
def get_constraints() -> Tuple[Type[AbstractConstraint], ...]:
    return tuple(
        sorted(
            get_all_subclasses(AbstractConstraint, skip_abstract=True),  # type: ignore
            key=lambda cls: cls.name(),
        )
    )


@dataclass
class ConstraintRule(Optimizable):
    constraint: Optional[AbstractConstraint] = None
    constraint_name: str = ""
    args: Tuple[Any, ...] = tuple()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    inverted: bool = False  # whether the test result should be inverted

    def is_droppable(self) -> bool:
        return not (self.constraint and not self.constraint.is_droppable())

    def optimize(self) -> Generator[Optimizable, None, None]:
        return
        yield

    def test(self, view: sublime.View) -> bool:
        assert self.constraint

        try:
            result = self.constraint.test(view)
        except AlwaysTruthyException:
            return True
        except AlwaysFalsyException:
            return False
        except Exception as e:
            print(f"[{PLUGIN_NAME}] ConstraintRule Exception: {e}")
            return False

        return not result if self.inverted else result

    @classmethod
    def make(cls, constraint_rule: ST_ConstraintRule) -> ConstraintRule:
        """Build this object with the `constraint_rule`."""
        obj = cls()

        if args := constraint_rule.get("args"):
            # make sure args is always a tuple
            obj.args = tuple(args) if isinstance(args, list) else (args,)

        if kwargs := constraint_rule.get("kwargs"):
            obj.kwargs = kwargs

        if (inverted := constraint_rule.get("inverted")) is not None:
            obj.inverted = bool(inverted)

        if constraint := constraint_rule.get("constraint"):
            obj.constraint_name = constraint
            if constraint_class := find_constraint(constraint):
                obj.constraint = constraint_class(*obj.args, **obj.kwargs)

        return obj


class AbstractConstraint(ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    @final
    @classmethod
    def name(cls) -> str:
        """The nickname of this class. Converts "FooBarConstraint" into "foo_bar" by default."""
        return camel_to_snake(remove_suffix(cls.__name__, "Constraint"))

    @final
    @classmethod
    def is_supported(cls, obj: Any) -> bool:
        """Determines whether this class supports `obj`."""
        return str(obj) == cls.name()

    def is_droppable(self) -> bool:
        """
        Determines whether this object is droppable.
        If it's droppable, then it may be dropped by who holds it during optimizing.
        """
        return False

    @abstractmethod
    def test(self, view: sublime.View) -> bool:
        """Tests whether the `view` passes this constraint."""

    @final
    def _handled_args(self, normalizer: Optional[Callable[[T], T]] = None) -> Tuple[T, ...]:
        """Filter falsy args and normalize them. Note that `0`, `""` and `None` are falsy."""
        args: Iterable[T] = filter(None, self.args)
        if normalizer:
            args = map(normalizer, args)
        return tuple(args)

    @final
    @staticmethod
    def _handled_comparator(comparator: str) -> Optional[Callable[[Any, Any], bool]]:
        """Convert the comparator string into a callable."""
        if comparator in {"<", "lt"}:
            return operator.lt
        if comparator in {"<=", "le", "lte"}:
            return operator.le
        if comparator in {">=", "ge", "gte"}:
            return operator.ge
        if comparator in {">", "gt"}:
            return operator.gt
        if comparator in {"=", "==", "===", "eq", "is"}:
            return operator.eq
        if comparator in {"!", "!=", "!==", "<>", "ne", "neq", "not"}:
            return operator.ne
        return None

    @final
    @staticmethod
    def _handled_regex(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Pattern[str]:
        """Returns compiled regex object from `args` and `kwargs.regex_flags`."""
        return compile_regex(
            merge_regexes(args),
            parse_regex_flags(kwargs.get("regex_flags", ["MULTILINE"])),
        )

    @final
    @staticmethod
    def _handled_case_insensitive(kwargs: Dict[str, Any]) -> bool:
        """Returns `case_insensitive` in `kwars`. Defaulted to platform's specification."""
        return bool(kwargs.get("case_insensitive", ST_PLATFORM in {"windows", "osx"}))

    @final
    @staticmethod
    def get_view_snapshot(view: sublime.View) -> ViewSnapshot:
        """Gets the cached information for the `view`."""
        snapshot = ViewSnapshotCollection.get_by_view(view)
        assert snapshot  # our workflow guarantees this won't be None
        return snapshot

    @final
    @staticmethod
    def find_parent_with_sibling(base: Union[str, Path], sibling: str, *, use_exists: bool = False) -> Optional[Path]:
        """Find the first parent directory which contains `sibling`."""
        path = Path(base).resolve()

        if use_exists:
            checker = Path.exists
        else:
            checker = Path.is_dir if sibling.endswith(("\\", "/")) else Path.is_file

        return first(path.parents, lambda p: checker(p / sibling))


class AlwaysTruthyException(Exception):
    """Used to indicate that the constraint returns `True` no matter it's inverted or not."""


class AlwaysFalsyException(Exception):
    """Used to indicate that the constraint returns `False` no matter it's inverted or not."""
