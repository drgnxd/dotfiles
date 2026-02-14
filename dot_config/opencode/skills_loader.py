#!/usr/bin/env python3
"""Skills loader with thinking framework support.

Supports both original and optimized catalog key names.
Loads core skills, always-load skills, and task-specific skills
within a token budget. Supports presets and ordered loading.

Usage: run as script or import SkillsLoader

Internal modules:
  - skills_catalog: Catalog loading, validation, skill lookups
  - skills_matcher: Keyword matching, thinking mode detection
  - skills_formatter: Output formatting
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from skills_catalog import SkillsCatalog, SkillsLoaderError
from skills_formatter import SkillsFormatter
from skills_matcher import SkillsMatcher, ThinkingMode as ThinkingMode


class SkillsLoader:
    """Load and manage AI agent skills with thinking framework support.

    This class delegates to specialized modules:
      - SkillsCatalog: catalog/core loading and validation
      - SkillsMatcher: keyword matching and thinking mode detection
      - SkillsFormatter: output formatting
    """

    CORE_TOKENS_ESTIMATE = 200  # Fallback if estimation fails

    def __init__(self, base_path: Path = Path(__file__).resolve().parent):
        """Initialize the skills loader.

        Args:
            base_path: Directory containing skills YAML files.
        """
        self.base_path = base_path
        self._catalog_mod = SkillsCatalog(base_path)
        self._matcher = SkillsMatcher(self._catalog_mod)
        self._formatter = SkillsFormatter(self._catalog_mod.catalog)

        # Expose catalog and core for backward compatibility with tests
        self.catalog = self._catalog_mod.catalog
        self.core = self._catalog_mod.core

    # --- Delegated Methods (backward-compatible public API) ---

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count from text content."""
        return SkillsFormatter.estimate_tokens(text)

    def _load_skill_content(self, skill_path: Path) -> Optional[Dict]:
        """Load a single skill file."""
        return self._catalog_mod.load_skill_content(skill_path)

    def _get_catalog_value(self, meta: Dict, key: str, default=None):
        """Get value from catalog with key aliasing support."""
        return self._catalog_mod.get_value(meta, key, default)

    def _parse_keywords(self, meta: Dict) -> List[str]:
        """Parse keywords from catalog metadata."""
        return self._catalog_mod.parse_keywords(meta)

    def _matches_keywords(self, task: str, keywords: List[str]) -> bool:
        """Check if task matches any keyword."""
        return self._matcher.matches_keywords(task, keywords)

    def _catalog_is_flat(self, catalog_data: Dict) -> bool:
        """Detect flat vs categorized catalog."""
        return self._catalog_mod.catalog_is_flat(catalog_data)

    def _detect_thinking_mode(self, task: str) -> str:
        """Detect appropriate thinking mode."""
        return self._matcher.detect_thinking_mode(task)

    def _analyze_task_keywords(self, task: str) -> List[Tuple[str, Dict]]:
        """Analyze task and return matching skills."""
        return self._matcher.analyze_task_keywords(task)

    def _resolve_always_load(
        self, task_skills: List[Tuple[str, Dict]]
    ) -> List[Tuple[str, Dict]]:
        """Prepend always-load skills."""
        return self._matcher.resolve_always_load(task_skills)

    def _find_skill_in_catalog(
        self, catalog_data: Dict, skill_name: str
    ) -> Optional[Dict]:
        """Find skill metadata by name."""
        return self._catalog_mod.find_skill(catalog_data, skill_name)

    def validate_catalog(self, warn_duplicate_keywords: bool = False) -> List[str]:
        """Validate the catalog structure and references."""
        return self._catalog_mod.validate(warn_duplicate_keywords)

    def _resolve_preset(self, preset: str) -> List[Tuple[str, Dict]]:
        """Resolve a preset name to skill list."""
        return self._catalog_mod.resolve_preset(preset)

    # --- Main Entry ---

    def load_for_task(self, task: str, preset: Optional[str] = None) -> str:
        """Load relevant skills for a given task.

        Flow:
            1. Detect thinking mode from task description
            2. Find keyword-matched skills (or use preset)
            3. Prepend always-load skills
            4. Load each skill within token budget
            5. Format and return output

        Args:
            task: Task description to analyze.
            preset: Optional preset name to use instead of keyword matching.

        Returns:
            Formatted string with all loaded skills and metadata.
        """
        thinking_mode = self._detect_thinking_mode(task)
        max_tokens = self._catalog_mod.get_max_tokens()

        # Resolve skill list: preset or keyword-matched
        if preset is not None:
            task_skills = self._resolve_preset(preset)
        else:
            task_skills = self._analyze_task_keywords(task)

        all_skills = self._resolve_always_load(task_skills)

        # Core content with measured token count
        core_content = yaml.dump(self.core, default_flow_style=False)
        tokens_used = self._estimate_tokens(core_content)

        # Load each skill within budget
        loaded_skills: List[Tuple[str, str, Optional[Dict]]] = []
        for skill_name, meta in all_skills:
            skill_path = self.base_path / "skills" / meta.get("path", "")
            skill_content = self._load_skill_content(skill_path)

            if skill_content is None:
                status = "missing" if not skill_path.exists() else "error"
                loaded_skills.append((skill_name, status, None))
                continue

            # Use measured tokens, fall back to catalog value
            skill_text = yaml.dump(skill_content, default_flow_style=False)
            measured_tokens = self._estimate_tokens(skill_text)
            raw_catalog_tokens = self._get_catalog_value(meta, "tokens", 0)
            try:
                catalog_tokens = int(raw_catalog_tokens)
            except (TypeError, ValueError):
                catalog_tokens = 0
            skill_tokens = max(measured_tokens, catalog_tokens)

            if tokens_used + skill_tokens > max_tokens:
                loaded_skills.append((skill_name, "skipped", None))
                continue

            loaded_skills.append((skill_name, "loaded", skill_content))
            tokens_used += skill_tokens

        return self._formatter.format_output(
            core_content, thinking_mode, loaded_skills, tokens_used, max_tokens
        )


def _run_validation() -> int:
    loader = SkillsLoader()
    errors = loader.validate_catalog()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("skills_catalog.yaml validation passed")
    return 0


def main() -> int:
    if "--validate" in sys.argv[1:]:
        return _run_validation()

    if "--validate-strict" in sys.argv[1:]:
        loader = SkillsLoader()
        errors = loader.validate_catalog(warn_duplicate_keywords=True)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print("skills_catalog.yaml strict validation passed")
        return 0

    # Check for preset argument: --preset=py_dev
    preset = None
    for arg in sys.argv[1:]:
        if arg.startswith("--preset="):
            preset = arg.split("=", 1)[1]

    loader = SkillsLoader()

    if preset:
        print(f"Loading preset: {preset}")
        try:
            result = loader.load_for_task("preset task", preset=preset)
            print(result)
        except SkillsLoaderError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        return 0

    test_tasks = [
        "ls -la",
        "Create a Python script to parse CSV files",
        "Design a fault-tolerant microservices architecture",
    ]

    for task in test_tasks:
        print(f"\n{'=' * 60}")
        print(f"Task: {task}")
        print(f"{'=' * 60}")
        result = loader.load_for_task(task)
        print(result[:800])
        print("[... truncated ...]")
        print(f"Total length: {len(result)} chars (~{len(result) // 4} tokens)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
