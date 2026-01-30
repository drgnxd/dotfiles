#!/usr/bin/env python3
"""Simple skills loader for token-aware loading.

Usage: run as script or import SkillsLoader
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml


class SkillsLoaderError(Exception):
    """Base exception for skills loader errors."""

    pass


class SkillsLoader:
    """Load and manage AI agent skills based on task descriptions."""

    # Base tokens used for core skills (estimated)
    CORE_TOKENS_ESTIMATE = 500

    def __init__(self, base_path: Path = Path(__file__).resolve().parent):
        """Initialize the skills loader.

        Args:
            base_path: Directory containing skills YAML files. Defaults to the
                      directory containing this script.
        """
        self.base_path = base_path
        self.catalog = self._load_catalog()
        self.core = self._load_core()

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
            content = path.read_text(encoding="utf-8")
            return yaml.safe_load(content)
        except Exception as e:
            raise SkillsLoaderError(f"Failed to load {path}: {e}")

    def _load_catalog(self) -> Dict:
        """Load the skills catalog from skills_catalog.yaml.

        Returns:
            Catalog dictionary with skill metadata.

        Raises:
            SkillsLoaderError: If catalog file is missing or invalid.
        """
        catalog_path = self.base_path / "skills_catalog.yaml"
        catalog = self._load_yaml_file(catalog_path)

        if catalog is None:
            raise SkillsLoaderError(f"Catalog file not found: {catalog_path}")

        return catalog

    def _load_core(self) -> Dict:
        """Load core skills from skills_core.yaml.

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

    def _analyze_task_keywords(self, task: str) -> List[Tuple[str, Dict]]:
        """Analyze task and return matching skills based on keywords.

        Args:
            task: Task description to analyze.

        Returns:
            List of tuples containing (skill_name, skill_metadata) for matched skills.
        """
        task_lower = task.lower()
        skills_to_load = []

        catalog_data = self.catalog.get("catalog", {})
        for category, skills in catalog_data.items():
            for skill_name, meta in skills.items():
                keywords = meta.get("trigger_keywords", [])
                if any(kw in task_lower for kw in keywords):
                    skills_to_load.append((skill_name, meta))

        return skills_to_load

    def _load_skill_content(self, skill_name: str, skill_path: Path) -> Optional[Dict]:
        """Load a single skill file.

        Args:
            skill_name: Name of the skill for error reporting.
            skill_path: Path to the skill YAML file.

        Returns:
            Parsed skill content as dict, or None if loading fails.
        """
        if not skill_path.exists():
            return None

        try:
            return yaml.safe_load(skill_path.read_text())
        except Exception:
            return None

    def _format_output(
        self,
        core_content: str,
        skills: List[Tuple[str, str, Optional[Dict]]],
        tokens_used: int,
        max_tokens: int,
    ) -> str:
        """Format the final output with core skills and loaded skills.

        Args:
            core_content: YAML-formatted core skills content.
            skills: List of tuples containing (skill_name, status, skill_content).
                   Status can be 'loaded', 'skipped', 'missing', or 'error'.
            tokens_used: Total tokens used.
            max_tokens: Maximum token budget.

        Returns:
            Formatted output string.
        """
        output = ["# Core Skills (Always Loaded)\n"]
        output.append(core_content)

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
        return "".join(output)

    def load_for_task(self, task: str) -> str:
        """Load relevant skills based on task description.

        Analyzes the task description to find matching skills based on keywords,
        then loads them while respecting the token budget.

        Args:
            task: Task description to analyze.

        Returns:
            Formatted string containing loaded skills and token usage info.
        """
        tokens_used = self.CORE_TOKENS_ESTIMATE
        max_tokens = self.catalog.get("load_strategy", {}).get("max_tokens", 8000)

        # Analyze task and find matching skills
        skills_to_load = self._analyze_task_keywords(task)

        # Prepare core content
        core_content = yaml.dump(self.core, default_flow_style=False)

        # Track loaded skills with their status
        loaded_skills: List[Tuple[str, str, Optional[Dict]]] = []

        # Load each matched skill within token budget
        for skill_name, meta in skills_to_load:
            skill_tokens = meta.get("tokens", 1000)

            # Check token budget
            if tokens_used + skill_tokens > max_tokens:
                loaded_skills.append((skill_name, "skipped", None))
                break

            # Load skill content
            skill_path = self.base_path / "skills" / meta.get("path", "")
            skill_content = self._load_skill_content(skill_name, skill_path)

            if skill_content is None:
                if not skill_path.exists():
                    loaded_skills.append((skill_name, "missing", None))
                else:
                    loaded_skills.append((skill_name, "error", None))
            else:
                loaded_skills.append((skill_name, "loaded", skill_content))

            tokens_used += skill_tokens

        return self._format_output(core_content, loaded_skills, tokens_used, max_tokens)


if __name__ == "__main__":
    loader = SkillsLoader()
    task1 = "Create a Python script to parse CSV files"
    print(loader.load_for_task(task1))
