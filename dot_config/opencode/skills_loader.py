#!/usr/bin/env python3
"""Skills loader with thinking framework support.

Loads core skills, always-load skills (japanese, thinking),
and task-specific skills within a token budget.
Detects thinking mode from task description.

Usage: run as script or import SkillsLoader
"""

from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple
import yaml


class SkillsLoaderError(Exception):
    """Base exception for skills loader errors."""

    pass


class ThinkingMode:
    """Thinking mode constants."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class SkillsLoader:
    """Load and manage AI agent skills with thinking framework support."""

    CORE_TOKENS_ESTIMATE = 500

    def __init__(self, base_path: Path = Path(__file__).resolve().parent):
        """Initialize the skills loader.

        Args:
            base_path: Directory containing skills YAML files.
        """
        self.base_path = base_path
        self.catalog = self._load_catalog()
        self.core = self._load_core()

    # --- YAML Loading ---

    def _load_yaml_file(self, path: Path) -> Optional[Dict]:
        """Safely load a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            Parsed YAML content as dict, or None if file doesn't exist.

        Raises:
            SkillsLoaderError: If file exists but cannot be read or parsed.
        """
        if not path.exists():
            return None
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise SkillsLoaderError(f"Failed to load {path}: {e}")

    def _load_catalog(self) -> Dict:
        """Load the skills catalog.

        Returns:
            Catalog dictionary.

        Raises:
            SkillsLoaderError: If catalog file is missing or invalid.
        """
        catalog_path = self.base_path / "skills_catalog.yaml"
        catalog = self._load_yaml_file(catalog_path)
        if catalog is None:
            raise SkillsLoaderError(f"Catalog file not found: {catalog_path}")
        return catalog

    def _load_core(self) -> Dict:
        """Load core skills.

        Returns:
            Core skills dictionary.

        Raises:
            SkillsLoaderError: If core file is missing or invalid.
        """
        core_path = self.base_path / "skills_core.yaml"
        core = self._load_yaml_file(core_path)
        if core is None:
            raise SkillsLoaderError(f"Core skills file not found: {core_path}")
        return core

    def _load_skill_content(self, skill_path: Path) -> Optional[Dict]:
        """Load a single skill file.

        Args:
            skill_path: Path to the skill YAML file.

        Returns:
            Parsed skill content as dict, or None if loading fails.
        """
        if not skill_path.exists():
            return None
        try:
            return yaml.safe_load(skill_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    # --- Thinking Mode Detection ---

    def _detect_thinking_mode(self, task: str) -> str:
        """Detect appropriate thinking mode based on task description.

        Checks complex patterns first (most specific), then simple,
        then medium. Falls back to medium for ambiguous tasks.

        Args:
            task: Task description to analyze.

        Returns:
            One of ThinkingMode constants.
        """
        task_lower = task.lower()
        mode_config = self.catalog.get("thinking_mode_auto_detect", {})

        # Complex first (highest specificity)
        for pattern in mode_config.get("complex", {}).get("patterns", []):
            if re.search(pattern, task_lower):
                return ThinkingMode.COMPLEX

        # Simple patterns
        for pattern in mode_config.get("simple", {}).get("patterns", []):
            if re.search(pattern, task_lower):
                return ThinkingMode.SIMPLE

        # Medium patterns
        for pattern in mode_config.get("medium", {}).get("patterns", []):
            if re.search(pattern, task_lower):
                return ThinkingMode.MEDIUM

        # Default: medium
        return ThinkingMode.MEDIUM

    # --- Task Analysis ---

    def _analyze_task_keywords(self, task: str) -> List[Tuple[str, Dict]]:
        """Analyze task and return matching skills based on keywords.

        Args:
            task: Task description to analyze.

        Returns:
            List of (skill_name, skill_metadata) sorted by priority.
        """
        task_lower = task.lower()
        skills_to_load: List[Tuple[str, Dict]] = []

        catalog_data = self.catalog.get("catalog", {})
        for _category, skills in catalog_data.items():
            for skill_name, meta in skills.items():
                keywords = meta.get("trigger_keywords", [])
                if any(kw in task_lower for kw in keywords):
                    skills_to_load.append((skill_name, meta))

        # Priority sort: high-priority skills first
        skills_to_load.sort(key=lambda x: 0 if x[1].get("priority") == "high" else 1)
        return skills_to_load

    def _resolve_always_load(
        self, task_skills: List[Tuple[str, Dict]]
    ) -> List[Tuple[str, Dict]]:
        """Prepend always-load skills that aren't already in the task list.

        Reads load_strategy.always from catalog.
        Skips 'skills_core.yaml' (loaded separately via _load_core).

        Args:
            task_skills: Skills already matched by keyword analysis.

        Returns:
            Combined list with always-load skills prepended.
        """
        always_names = self.catalog.get("load_strategy", {}).get("always", [])
        loaded_names = {name for name, _ in task_skills}
        catalog_data = self.catalog.get("catalog", {})

        prepend: List[Tuple[str, Dict]] = []
        for always_name in always_names:
            if always_name == "skills_core.yaml" or always_name in loaded_names:
                continue
            # Find in catalog
            for _category, skills in catalog_data.items():
                if always_name in skills:
                    prepend.append((always_name, skills[always_name]))
                    loaded_names.add(always_name)
                    break

        return prepend + task_skills

    # --- Output Formatting ---

    def _format_thinking_header(self, mode: str) -> str:
        """Format thinking mode header for output.

        Args:
            mode: Detected thinking mode.

        Returns:
            Formatted header string.
        """
        mode_config = self.catalog.get("thinking_mode_auto_detect", {}).get(mode, {})
        overhead = mode_config.get("overhead_budget", "?")

        return (
            f"\n# Thinking Mode: {mode.upper()}\n# Overhead budget: {overhead} tokens\n"
        )

    def _format_output(
        self,
        core_content: str,
        thinking_mode: str,
        skills: List[Tuple[str, str, Optional[Dict]]],
        tokens_used: int,
        max_tokens: int,
    ) -> str:
        """Format the final output.

        Args:
            core_content: YAML-formatted core skills.
            thinking_mode: Detected thinking mode.
            skills: List of (skill_name, status, content) tuples.
            tokens_used: Total tokens consumed.
            max_tokens: Token budget ceiling.

        Returns:
            Complete formatted output string.
        """
        output = ["# Core Skills (Always Loaded)\n"]
        output.append(core_content)
        output.append(self._format_thinking_header(thinking_mode))

        for skill_name, status, skill_content in skills:
            if status == "loaded" and skill_content is not None:
                output.append(f"\n# {skill_name.title()}\n")
                output.append(yaml.dump(skill_content, default_flow_style=False))
            elif status == "skipped":
                output.append(f"\n# {skill_name.title()} (skipped - token limit)\n")
            elif status == "missing":
                output.append(f"\n# {skill_name.title()} (missing file)\n")
            elif status == "error":
                output.append(f"\n# {skill_name.title()} (error loading)\n")

        output.append(f"\n# Tokens used: {tokens_used}/{max_tokens}\n")
        output.append(f"# Thinking mode: {thinking_mode}\n")
        return "".join(output)

    # --- Main Entry ---

    def load_for_task(self, task: str) -> str:
        """Load relevant skills for a given task.

        Flow:
            1. Detect thinking mode from task description
            2. Find keyword-matched skills
            3. Prepend always-load skills
            4. Load each skill within token budget
            5. Format and return output

        Args:
            task: Task description to analyze.

        Returns:
            Formatted string with all loaded skills and metadata.
        """
        thinking_mode = self._detect_thinking_mode(task)
        tokens_used = self.CORE_TOKENS_ESTIMATE
        max_tokens = self.catalog.get("load_strategy", {}).get("max_tokens", 5000)

        # Resolve full skill list (always-load + keyword-matched)
        all_skills = self._resolve_always_load(self._analyze_task_keywords(task))

        # Core content
        core_content = yaml.dump(self.core, default_flow_style=False)

        # Load each skill within budget
        loaded_skills: List[Tuple[str, str, Optional[Dict]]] = []
        for skill_name, meta in all_skills:
            skill_tokens = meta.get("tokens", 1000)

            if tokens_used + skill_tokens > max_tokens:
                loaded_skills.append((skill_name, "skipped", None))
                continue

            skill_path = self.base_path / "skills" / meta.get("path", "")
            skill_content = self._load_skill_content(skill_path)

            if skill_content is None:
                status = "missing" if not skill_path.exists() else "error"
                loaded_skills.append((skill_name, status, None))
            else:
                loaded_skills.append((skill_name, "loaded", skill_content))

            tokens_used += skill_tokens

        return self._format_output(
            core_content, thinking_mode, loaded_skills, tokens_used, max_tokens
        )


if __name__ == "__main__":
    loader = SkillsLoader()

    test_tasks = [
        "ls -la",
        "Create a Python script to parse CSV files",
        "Design a fault-tolerant microservices architecture",
    ]

    for task in test_tasks:
        print(f"\n{'=' * 60}")
        print(f"Task: {task}")
        print(f"{'=' * 60}")
        print(loader.load_for_task(task)[:800])
        print("[... truncated ...]")
