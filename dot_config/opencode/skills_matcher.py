"""Keyword matching, thinking mode detection, and task analysis."""

import re
from typing import Any, Dict, List, Tuple

# Import the catalog value accessor protocol to avoid circular deps
from skills_catalog import SkillsCatalog


class ThinkingMode:
    """Thinking mode constants."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class SkillsMatcher:
    """Handles keyword matching and thinking mode detection."""

    def __init__(self, catalog: SkillsCatalog):
        self._catalog = catalog

    def matches_keywords(self, task: str, keywords: List[str]) -> bool:
        """Check if task matches any keyword with word boundary awareness.

        Handles three keyword types:
        - File extensions (e.g. '.py', '\\.py'): substring match
        - Regex patterns: regex match
        - Plain words: word boundary match to avoid substring false positives
        """
        for kw in keywords:
            if kw.startswith(".") or kw.startswith("\\."):
                clean_ext = kw.lstrip("\\")
                if clean_ext in task:
                    return True
            else:
                pattern = r"(?:^|[^a-z0-9_])" + re.escape(kw) + r"(?:[^a-z0-9_]|$)"
                if re.search(pattern, task):
                    return True
        return False

    def detect_thinking_mode(self, task: str) -> str:
        """Detect appropriate thinking mode based on task description.

        Checks complex first (most specific), then simple, then medium.
        Falls back to medium for ambiguous tasks.
        """
        task_lower = task.lower()
        mode_config = self._catalog.catalog.get(
            "thinking_mode_auto_detect"
        ) or self._catalog.catalog.get("think_mode", {})

        # Complex first (highest specificity)
        complex_cfg = mode_config.get("complex", {})
        for pattern in complex_cfg.get("patterns") or complex_cfg.get("pat", []):
            if re.search(pattern, task_lower):
                return ThinkingMode.COMPLEX

        # Simple patterns
        simple_cfg = mode_config.get("simple", {})
        for pattern in simple_cfg.get("patterns") or simple_cfg.get("pat", []):
            if re.search(pattern, task_lower):
                return ThinkingMode.SIMPLE

        # Medium patterns
        medium_cfg = mode_config.get("medium", {})
        for pattern in medium_cfg.get("patterns") or medium_cfg.get("pat", []):
            if re.search(pattern, task_lower):
                return ThinkingMode.MEDIUM

        return ThinkingMode.MEDIUM

    def analyze_task_keywords(self, task: str) -> List[Tuple[str, Dict]]:
        """Analyze task and return matching skills based on keywords.

        Returns list of (skill_name, skill_metadata) sorted by priority.
        """
        task_lower = task.lower()
        skills_to_load: List[Tuple[str, Dict]] = []

        catalog_data = self._catalog.get_catalog_data()

        for skill_name, meta in self._catalog.iterate_skills(catalog_data):
            if not isinstance(meta, dict):
                continue
            keywords = self._catalog.parse_keywords(meta)
            if self.matches_keywords(task_lower, keywords):
                skills_to_load.append((skill_name, meta))

        def priority_key(x: Tuple[str, Dict]) -> Tuple[int, int]:
            pri = self._catalog.get_value(x[1], "priority")
            raw_order = self._catalog.get_value(x[1], "order", 99)
            try:
                order_val = int(raw_order)
            except (TypeError, ValueError):
                order_val = 99
            pri_val = 0 if pri in ("high", "hi") else 1
            return (pri_val, order_val)

        skills_to_load.sort(key=priority_key)
        return skills_to_load

    def resolve_always_load(
        self, task_skills: List[Tuple[str, Dict]]
    ) -> List[Tuple[str, Dict]]:
        """Prepend always-load skills that aren't already in the task list."""
        load_cfg = self._catalog.get_load_config()
        always_names = load_cfg.get("always", [])
        loaded_names = {name for name, _ in task_skills}

        catalog_data = self._catalog.get_catalog_data()

        prepend: List[Tuple[str, Dict]] = []
        for always_name in always_names:
            if always_name == "skills_core.yaml" or always_name in loaded_names:
                continue
            meta = self._catalog.find_skill(catalog_data, always_name)
            if meta is not None:
                prepend.append((always_name, meta))
                loaded_names.add(always_name)

        return prepend + task_skills
