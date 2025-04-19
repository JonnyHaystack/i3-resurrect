from abc import ABC
import json
import re
import shlex
from typing import Sequence, TypeVar

from . import util

# Window properties and value to add to score when match is found.
CRITERIA = {
    "window_role": 1,
    "class": 2,
    "instance": 3,
    "title": 10,
}


class Rule(ABC):
    T = TypeVar("T", bound="Rule")

    def __init__(self, filters: dict):
        self.filters = filters

    def get_match_score(self, window_properties: dict) -> int:
        """
        Score window command mapping match based on which criteria match.

        Scoring is done based on which criteria are considered "more specific" and thus have higher
        weight assigned.
        """
        score = 0
        for criterion in CRITERIA:
            if criterion in self.filters:
                # Score is zero if there are any non-matching criteria.
                if (
                    criterion not in window_properties
                    or re.match(self.filters[criterion], window_properties[criterion])
                    is None
                ):
                    return 0
                score += CRITERIA[criterion]
        return score

    @classmethod
    def find_best_matching_rule(
        cls: type[T], window_properties: dict, rules: Sequence[T]
    ) -> T | None:
        # Find the mapping that gets the highest score.
        current_score = 0
        best_match = None
        for rule in rules:
            # Calculate score.
            score = rule.get_match_score(window_properties)

            # Update best match.
            if score > current_score:
                current_score = score
                best_match = rule

        return best_match


class WindowCommandMapping(Rule):
    def __init__(self, filters: dict, command: str | list[str]):
        super().__init__(filters)
        self.command = command

    def format_cmdline(self, cmdline: list[str]) -> list[str]:
        try:
            if self.command is None:
                return []
            if isinstance(self.command, list):
                # If replacement command is array, substitute original args into each arg of replacement
                # command template.
                return [
                    arg.format(*cmdline, args=" ".join(cmdline[1:]))
                    for arg in self.command
                ]
            else:
                # If command mapping is string, just do the substitution once, then split into array so
                # it's in a normalized form.
                return shlex.split(
                    self.command.format(*cmdline, args=" ".join(cmdline[1:]))
                )
        except IndexError:
            util.eprint(
                "IndexError occurred while processing command mapping:\n"
                f"  Mapping: {json.dumps(self)}\n"
                f"  Process cmdline: {cmdline}"
            )
            return []


class WindowSwallowMapping(Rule):
    def __init__(self, filters: dict, swallow_criteria: dict[str, str] | list[str]):
        super().__init__(filters)
        self.swallow_criteria = swallow_criteria

    def get_swallow_values(self, window_properties: dict) -> dict:
        if isinstance(self.swallow_criteria, list):
            # For list-style swallow criteria, use values from window properties.
            swallow_values = {
                criteria: f"^{re.escape(window_properties[criteria])}$"
                for criteria in self.swallow_criteria
            }

            return swallow_values
        else:
            # Use swallow criteria dict values as defined by user.
            swallow_values = self.swallow_criteria

            # But for swallow criteria where value is null or empty string, fall back to value from
            # window properties.
            for criteria, value in swallow_values.items():
                if value is None or value == "":
                    swallow_values[criteria] = (
                        f"^{re.escape(window_properties[criteria])}$"
                    )

            return swallow_values
