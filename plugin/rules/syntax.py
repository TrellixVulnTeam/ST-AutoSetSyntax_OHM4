from __future__ import annotations

# __future__ must be the first import
from ..constant import VERSION
from ..helper import find_syntax_by_syntax_like
from ..helper import first
from ..types import Optimizable, ST_SyntaxRule
from .match import MatchRule
from dataclasses import dataclass
from typing import Any, Generator, Iterable, List, Optional, Set, Tuple
import sublime


@dataclass
class SyntaxRule(Optimizable):
    comment: str = ""
    syntax: Optional[sublime.Syntax] = None
    syntaxes_name: Optional[Tuple[str, ...]] = tuple()
    selector: str = "text.plain"
    on_events: Optional[Set[str]] = None
    root_rule: Optional[MatchRule] = None

    def is_droppable(self) -> bool:
        return not (self.syntax and self.on_events != [] and self.root_rule)

    def optimize(self) -> Generator[Optimizable, None, None]:
        if self.root_rule:
            if self.root_rule.is_droppable():
                yield self.root_rule
                self.root_rule = None
            else:
                yield from self.root_rule.optimize()
                if self.root_rule.is_droppable():
                    yield self.root_rule
                    self.root_rule = None

    def test(self, view: sublime.View, event_name: Optional[str] = None) -> bool:
        if event_name and self.on_events is not None and event_name not in self.on_events:
            return False

        if not view.match_selector(0, self.selector):
            return False

        assert self.root_rule
        return self.root_rule.test(view)

    @classmethod
    def make(cls, syntax_rule: ST_SyntaxRule) -> SyntaxRule:
        """Build this object with the `syntax_rule`."""
        obj = cls()

        if comment := syntax_rule.get("comment"):
            obj.comment = str(comment)

        syntaxes = syntax_rule.get("syntaxes", [])
        if isinstance(syntaxes, str):
            syntaxes = [syntaxes]
        obj.syntaxes_name = tuple(syntaxes)
        if target_syntax := first(map(find_syntax_by_syntax_like, syntaxes)):
            obj.syntax = target_syntax

        # note that an empty string selector should match any scope
        if (selector := syntax_rule.get("selector")) is not None:
            obj.selector = selector

        if (on_events := syntax_rule.get("on_events")) is not None:
            if isinstance(on_events, str):
                on_events = [on_events]
            obj.on_events = set(on_events)

        if match_rule_compiled := MatchRule.make(syntax_rule):
            obj.root_rule = match_rule_compiled

        return obj


@dataclass
class SyntaxRuleCollection(Optimizable):
    version: str = VERSION
    rules: Tuple[SyntaxRule, ...] = tuple()

    def optimize(self) -> Generator[Any, None, None]:
        rules: List[SyntaxRule] = []
        for rule in self.rules:
            if rule.is_droppable():
                yield rule
                continue
            yield from rule.optimize()
            if rule.is_droppable():
                yield rule
            else:
                rules.append(rule)
        self.rules = tuple(rules)

    def test(self, view: sublime.View, event_name: Optional[str] = None) -> Optional[SyntaxRule]:
        return first(self.rules, lambda rule: rule.test(view, event_name))

    @classmethod
    def make(cls, syntax_rules: Iterable[ST_SyntaxRule]) -> SyntaxRuleCollection:
        """Build this object with the `syntax_rules`."""
        obj = cls()
        obj.rules = tuple(map(SyntaxRule.make, syntax_rules))
        return obj